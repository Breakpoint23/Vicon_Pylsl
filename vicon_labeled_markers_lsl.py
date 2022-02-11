from vicon_dssdk import ViconDataStream
import time
import pylsl
client=ViconDataStream.Client()
prev_frame_num=0
first_run=True
prev_time=time.time()

host_ip_address='localhost:801'

print('Connecting...')

while not client.IsConnected():
    client.Connect(host_ip_address)

print('Connected..')
while  not client.IsMarkerDataEnabled():
    client.EnableMarkerData()

print('Marker Data Enabled...')
while client.IsConnected():
    
    if client.GetFrame(): # gets new frame every iteration
        
        if first_run:
            
            # This is to set up the stream 
            
            
            frame_rate=client.GetFrameRate()  #This is optional, To set up the stream rate for PYLSL
            
            try:
                
                subject_name=client.GetSubjectNames()[0] # Get the first subject name 
                # for now this is only setup for one subject

                labeled_marker_count=len(client.GetLabeledMarkers())
                """
                here marker_labels contains tuples ((marker name, segment name))
                while marker_names only contains marker names
                """
                marker_labels=client.GetMarkerNames(subject_name)

                marker_names=[names[0] for names in marker_labels ]
                     
            except:
                    print("Marker Data is unabled")
                    break
                    

            """
            There will be 2 streams,
            one that contains data from markers | Vicon Labeled Markers
            and the other that contains data about whether at least one of the markers was occluded or not  | Occlusion stream
            """

            info=pylsl.StreamInfo(name='Vicon_Labeled_markers',channel_count=labeled_marker_count,nominal_srate=frame_rate,channel_format='string',desc=marker_names)
            info_occ=pylsl.StreamInfo(name='Occlusion_stream',channel_count=1,nominal_srate=0,type='Marker',channel_format='float32')
            outlet_occ=pylsl.StreamOutlet(info_occ)
            outlet=pylsl.StreamOutlet(info)

            # setting up buffers to store data temporarily to push in chunks
            buffer_data=[]
            buffer_occ=[]
            first_run=False
        else:
            try:
                temp_buffer=[]
                occlusion=[]
                """
                GetMarkerGlobalTranslation(subject_name,name) returns tuple ((x,y,z),Occlusion state) | x,y,z are in millimeters
                now to append the data in each channel , i'm are converting it to a string (pylsl did not take list of list as a sample per channel)
                so now the sample is list of strings  ['[marker data],marker name',...for each marker] (for Vicon Labeled Marker stream)
                while buffer_occ contains values True/False for whether any marker was occluded or not 
                """
                for name in marker_names:
                    data,occ=client.GetMarkerGlobalTranslation(subject_name,name) 
                    temp_buffer.append(f'{list(data)},{name}')
                    occlusion.append(occ)
                buffer_data.append(temp_buffer)
                buffer_occ.append(any(occlusion))
            except:
                print('Marker Data is not Enabled')
                break

        if time.time()-prev_time>2:
            """
            This block is for pushing the data in buffer to the stream every 2 seconds
            Here the buffers are also emptied 
            
            """
            outlet.push_chunk(buffer_data)
            outlet_occ.push_chunk(buffer_occ)
            buffer_data,buffer_occ=[],[]
            prev_time=time.time()
            
    else:
        pass

     

            

        
