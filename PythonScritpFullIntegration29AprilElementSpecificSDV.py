from odbAccess import*
#for ranning this script: go to working directory in your terminal where you have this odbFile>abaqus python ReadStressStrainDataFromODB.py
#python is an indentation sensitive language, carefullly read the comment and adjust the indentation 
odbFile = openOdb(path='./CDMTwoStep29April.odb')
assembly = odbFile.rootAssembly
parts =assembly.instances
part =assembly.instances.values()[0]    #0 means first instances

#Define the output file for each part
#------------Stress strain, stress component, strenght, accumulated shear strain and vom-mises stress ------------------
#stressStrainFile is the module that will be executed
StressStrainFile=open('./PythonCDMTwoStep29Aprillll.dat','w')

# get nodes number and nodal coordinates specific step of the simulation from the odb files
# Read the node locations for all nodes in all parts
# ----------------- Added Line for specific element SDV -----------------
target_element_id = 263  # <-- Change this to your desired element label
# ----------------------------------------------------------------------

lastStep=odbFile.steps['Step_2_Axial_Displacement']
xs = []  #Initializes an empty list to store the x-coordinates of nodes.
ys = []
zs = []

# loop over each node to get the dimension of the cubic and one node that lies in the specified surface
for key in parts.keys():      #for loop 1 starts, It processes all parts in the parts dictionary.
    for n in parts[key].nodes:  #for loop 2 starts, It processes all the nodes within each part.
        x,y,z = n.coordinates     #This extracts the x, y, and z coordinates of the current node n.
        xs.append(x)              #the append method is used to add a single element to the end of a list.
        ys.append(y)
        zs.append(z)
        #end of for loop 2
#end of loop 1


xmax = max(xs); xmin = min(xs)
ymax = max(ys); ymin = min(ys)
zmax = max(zs); zmin = min(zs)
width = xmax - xmin    # diameter of the circle
thick = ymax - ymin
length = zmax - zmin

print ('Dimension of the model is:' , width, thick, length)

# get the target node number(xmax) to read the displacement
#change it based on uniaxial load direction
for key in parts.keys():        #for loop 3 starts, It processes all parts in the parts dictionary.
    for n in parts[key].nodes:    #for loop 4 starts, It processes all the nodes within each part.
        z = n.coordinates[2]        #coordinate are already stored in python, python indexing starts from 0. 0=x, 1=y, 2=z
        if (z==zmax):
            print (' this is target node if loop')
            RFTargetNode=n.label
            break   
        #end of if statement
    # end of loop 4
# end of loop 3    
 

print ('Dimension of the model (x,y,z) is:' , width, thick, length)
print ('the target node is', RFTargetNode)

#Initialize the vectors for storing the data we are interested in.
DispVec=[] #this will store the strain data
RFVec=[]  #this will store the stress data calculated from reaction force
XDisp=[]
YDisp=[]  # based on the uniaxial direction may be used in future odb file analysis
ZDisp=[]
SDV1_1=[]   #it will catch all elements average SDV value
laststepDisp=0.0
incr=0

#loop over each time step (initialization), uses for cumlative time calculation for any specific increment and it is the first column of the data file
totaltime=0.0;
lastStepTime=0.0;

#for iStep in odbFile.steps.keys():   #for loop 5, find the all steps 
for iStep in ['Step_2_Axial_Displacement']:   #it will ran only in this specific step
    # start to extract the data
    print('Step:  ', iStep)
    lastStep=odbFile.steps[iStep]      # previous line: lastStep=odbFile.steps['Step-2-AxialLoading']

    for k in range(len(lastStep.frames)): #for loop 6, it will iterate all frame
        incr=incr+1   #"incr" is intialized as 0, 1 is added because python index starts from 1, so first index is 0+1=1, later 1 will be subtracted to get the abaqus equivalent 0 based indexing (reaction force calculation)
        print ('step increment', k)
        print ('total increment', incr)
        lastFrame = lastStep.frames[k]
        Time1=lastFrame.frameValue
        print('Time1', Time1) #Time1 is the time increment of a specific increment
        ReactionForce = lastFrame.fieldOutputs['RF']  # it will gather the reaction force for all nodes and all time increment
        DisPlacement=lastFrame.fieldOutputs['U']      # RF and U from odb file for all node are gathered and stored in python to the variable ReactionForce & DisPlacement variable respectfully
        DamageValue=lastFrame.fieldOutputs['SDV1']
        #end of for loop 6
        #end of for loop 5

        # apend zero value to the vectors which yet did not used but in future will be used
        # Append zero value to the vectors at each frame iteration (moved inside the loop)
        RFVec.append(0)
        #DispVec.append(0) #creates problem
        XDisp.append(0)
        YDisp.append(0)
        ZDisp.append(0)
        SDV1_1.append(0)
        #end of for loop 6
        #end of for loop 5

        # start to read data.
        # disp on the z+ face, all the nodes has the same value, one is enough
        #here Displacment(python stored data) is the fileld ouptut ['U']
        for v in DisPlacement.values:    #for loop 7 starts
            if v.nodeLabel == RFTargetNode:
                #DispVec.append(v.data[2]/width+laststepDisp)
                #Strain=v.data[0]/width
                Strain=v.data[2]/length    # python stored the data in 0 based indexing, index starts from x=0 so z=2
                DispVec.append(Strain)     #storing Strain value in DispVec which is previously initialized as "DispVec=[]"
            #end of if statement
        #end of for loop 7
        
        #this part will catch the damage variable of all elements average
        #for v in DamageValue.values:    #for loop 7 starts
         #        #SDV1_1[incr-1]=  v.data
        #         SDV1_1[incr-1]= SDV1_1[incr-1]+ v.data/8 # total 8 integration points
        #end of for loop 7


        # ----------------- New Block: Compute SDV1 of specific element-both reduced and full integration can be handeled -----------------
        target_sdv_val = None         # Initialize variable to hold the averaged SDV1 value of the target element
        integration_point_count = 0    # Counter to track how many integration points are found for the target element
        sdv_sum = 0.0          # Accumulator to sum all SDV1 values over the integration points of the target element

        for v in DamageValue.values:     # Loop through all SDV1 field values from the ODB 
            if v.elementLabel == target_element_id:  # Check if the current field value belongs to the target element
                sdv_sum += v.data   # Accumulate the SDV1 value for this integration point
                integration_point_count += 1   # Increase the count of integration points found for this element
        
        #After loop, calculate the average SDV1 over all integration points if any were found
        if integration_point_count > 0:
            target_sdv_val = sdv_sum / integration_point_count  # Compute average SDV1 for the element
        else:
            target_sdv_val = 0.0     # If no integration points found, set the SDV1 value to 0.0

        for v in ReactionForce.values:  #for loop 8 starts, ReactionForce(in python stored data) is the field output ['RF']
            if zs[v.nodeLabel-1] == zmax: #In Python, list indices start at 0, while Abaqus node labels usually start at 1. To access the correct entry in the zs list of python (which is 0-indexed), we subtract 1 from the node label.
                print('v.nodeLabel=',v.nodeLabel)
                print('v.nodeLabel-1=', v.nodeLabel-1)
                print('zmax=', zmax)
                print('zs[v.nodeLabel-1]=', zs[v.nodeLabel-1])
                #The "incr-1" is used here because Python indices start at 0, so this ensures the data is being appended to the correct index for the current time increment.
                #RFVec[incr-1]=RFVec[incr-1]+v.data[0]/thick #original, this line some up all reaction force which fullfill xmas condition
                #RFVec[incr-1]=RFVec[incr-1]+v.data[0]/(thick*length) #edited t
                #RFVec[incr-1]=RFVec[incr-1]+v.data[2]/(width*thick) #devided by circle area
                RFVec[incr-1]=RFVec[incr-1]+v.data[2]/(0.7854*width*width) #devided by circle area
                print ('stress from reaction force', RFVec[incr-1])
            #end of if statement
        #end of for loop 8
        
        #calculation cumulative time for the stress strain in any increment
        totalTime=lastStepTime+Time1

        #---start to write "----.dat" file
        #text file have three column (Current Time, Strain, Stress)
        #StressStrainFile.write('%10.8E     '  % totalTime)
        #StressStrainFile.write('%10.8E     '  % DispVec[incr-1])
        #StressStrainFile.write('%10.8E\n'  % RFVec[incr-1])
        #StressStrainFile.write('%10.8E\n   '  % SDV1_1[incr-1])

        StressStrainFile.write('%3.2E  '  % totalTime)
        StressStrainFile.write('%3.3E  '  % DispVec[incr-1])
        StressStrainFile.write('%3.3E  '  % RFVec[incr-1])
        #StressStrainFile.write('%3.4E  ' % SDV1_1[incr - 1])     # Global average SDV
        StressStrainFile.write('%3.4E\n' % target_sdv_val)      # Specific element SDVvalue
    #end of for loop 6

    #checking the total time
    laststepDisp=Strain
    lastStepTime=lastStepTime+Time1
#end of for loop 5
  
print('strian in this increment----------------------------------------------------------:', laststepDisp)
print('total time for force/strain applied to the system////////////////////////:', lastStepTime)
print('----------------------end of script----------------------------------------------------')

odbFile.close()                 # start to close files
StressStrainFile.close()        #---close odb files and stress strain file--
