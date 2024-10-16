import streamlit as st
from utils import * 
import plotly.io
import plotly.graph_objs as go
#import PIL 
import math
from PIL import Image
from matplotlib import pyplot as plt
import seaborn as sns
import statistics as stat
import os
import numpy as np
#import segmentation_models as sm
import cv2
from io import BytesIO
import imutils
from matplotlib import pyplot as plt
import pandas as pd
from scipy import ndimage
from scipy.optimize import curve_fit
from skimage import measure, color, io
import plotly.express as px
import plotly.figure_factory as ff
from plotly.subplots import make_subplots
from skimage import (
    filters,  morphology, img_as_float, img_as_ubyte, exposure
)
from skimage.draw import polygon
from stardist.models import StarDist2D
from stardist.plot import render_label
from csbdeep.utils import normalize
from st_aggrid import GridOptionsBuilder, AgGrid, GridUpdateMode, DataReturnMode
import time
import subprocess 
import warnings


st.warning('Navigating to another page from the sidebar will remove all selections from the current page')

if "button_clicked_movav" not in st.session_state:
    st.session_state.button_clicked_movav = False
    
if "button_clicked_movav_sta" not in st.session_state:
    st.session_state.button_clicked_movav_sta = False
    
def callback_movav():
    #Button was clicked
    st.session_state.button_clicked_movav = True
    
def callback_movav_sta():
    #Button was clicked
    st.session_state.button_clicked_movav_sta = True
    
if 'all_param_table' not in st.session_state:
    st.session_state.all_param_table = False
    
def callback_all_param_table():
   st.session_state.all_param_table = True
    
st.header('**_Intensity trace for multiple labels_**')
if 'raw_img_ani_pg_2' not in st.session_state:
    pass
else:
    raw_img_ani_pg_2 = st.session_state['raw_img_ani_pg_2']

if 'background_corr_pg_2' not in st.session_state:
    pass
else:
    background_corr_pg_2 = st.session_state['background_corr_pg_2']

if 'Collapsed_Image' not in st.session_state:
    pass
else:
    collapsed = st.session_state['Collapsed_Image']
    st.write('*_The Selected Image_*')
    st.image(collapsed,use_column_width=True,clamp = True)
    
if 'super_im_rgb_pg_2' not in st.session_state:
    pass
else:
    super_im_pg_2 = st.session_state['super_im_rgb_pg_2']
    st.write('*_Automatically labeled objects on the selected image_*')
    st.image(super_im_pg_2,use_column_width=True,clamp = True)

if 'final_label_rgb_pg_2' not in st.session_state:
    st.warning("Please generate the segmented and labeled image from the 'Preprocessing and Segmentation' page, and click on 'Single-cell Analysis' before proceeding")
else:
    label = st.session_state['final_label_rgb_pg_2']
    st.write('*_Automatically (or automatically plus manually) segmented and labeled objects on a black background_*')
    st.image(label,use_column_width=True,clamp = True)
    
if 'final_label_pg_2' not in st.session_state:
    pass
else:
    label_fin = st.session_state['final_label_pg_2']
    #st.image(label_fin,use_column_width=True,clamp = True)    

if 'label_list_pg_2' not in st.session_state:
    pass  
else:
    label_list_pg_2 = st.session_state['label_list_pg_2'] 
    if 'area_thres_x' not in st.session_state:
        st.session_state['area_thres_x'] = st.number_input("*_Choose the area threshold percentage_*", min_value=0.00, max_value=1.00, value=0.30,step = 0.01, format="%0.2f", help = f"Default is 0.3. Pixels below 30% of the maximum ({np.amax(raw_img_ani_pg_2)}) are not counted to get the bright area of labels", key='area_thres_1')
    if 'df_pro' not in st.session_state:
        #st.session_state['area_thres_x'] = st.number_input("*_Choose the area threshold percentage_*", min_value=0.00, max_value=1.00, value=0.30,step = 0.01, format="%0.2f", help = f"Default is 0.3. Pixels below 30% of the maximum ({np.amax(raw_img_ani_pg_2)}) are not counted to get the bright area of labels", key='area_thres_n')
        label_fin = st.session_state['final_label_pg_2']            
        data = list(np.unique(label_list_pg_2))        
        st.session_state['df_pro'] = pd.DataFrame(data, columns=['label'])
        col_arr = []
        props_pro = get_intensity(background_corr_pg_2[:, :, :, 0], [label_fin] * raw_img_ani_pg_2.shape[0])         
        props_pro = pd.DataFrame(props_pro).T
        props_pro['label'] = data

        for frames_pro in range(0,raw_img_ani_pg_2.shape[0]):
            col = []
            label_array = props_pro['label']
            intensity_im = background_corr_pg_2[frames_pro][:,:,0]
            #col_arr.append(intensity_im)                        
            for lab in label_array:
                mask_label = label_fin == lab
                #st.write(mask_label)
                intensity_values = intensity_im[mask_label]
                col.append(intensity_values)
            col_arr.append(np.array(col, dtype=object))
            
            df_single = props_pro
            #df_single['area'] = df_single[df_single['area']>df_single['intensity_mean'].mean()]['area']
            df_single.rename(columns = {frames_pro : f'intensity_mean_{frames_pro}'}, inplace=True)
            df_single[f'intensity_mean_{frames_pro}'] = np.round(df_single[f'intensity_mean_{frames_pro}'],3)

        st.session_state['df_pro'] = pd.merge(st.session_state['df_pro'], df_single, on = 'label', how = 'outer')                                                 
        
        ######## #################  ################# ###############Interactive table################################################################
        #df_pro = df_pro.drop(df_pro[df_pro['label'] == 255].index)
        for frame_col in range(0, raw_img_ani_pg_2.shape[0]):
            
            pixel_counts = []
            for label_val in st.session_state['df_pro']['label']:
                intensity_image = col_arr[frame_col][label_val-1]
                count = np.sum(np.greater(intensity_image, st.session_state['area_thres_x']*np.amax(raw_img_ani_pg_2[frame_col]))) #df_pro[f'intensity_mean_{frames_pro}'].mean()))
                pixel_counts.append(np.float64(count))
            #st.write(type(np.amax(raw_image_ani[frame_col])))
            pixel_var = f'Bright_pixel_area_{frame_col}'
            #df_pro[pixel_var] = pixel_counts
            pixel_counts_df = pd.DataFrame(pixel_counts,columns = [pixel_var],dtype = np.float64)
            st.session_state['df_pro'] = pd.concat((st.session_state['df_pro'], pixel_counts_df),axis=1)   

        st.dataframe(st.session_state['df_pro'], 1000, 200)
        dataframe_df = st.session_state['df_pro']
        get_data_indi = convert_df(st.session_state['df_pro'])
        st.download_button("Press to Download", get_data_indi, 'label_intensity_data.csv', "text/csv", key='label_download-get_data') 
    else:
        label_fin = st.session_state['final_label_pg_2']
        area_thres_x = st.number_input("*_Choose the area threshold percentage_*", min_value=0.00, max_value=1.00, value=0.3,step = 0.01, format="%0.2f", help = f"Default is 0.3. Pixels below 30% of the maximum ({np.amax(raw_img_ani_pg_2)}) are not counted to get the bright area of labels", key='area_thres')
        if area_thres_x == st.session_state['area_thres_x']:
            st.dataframe(st.session_state['df_pro'], 1000, 200)
            dataframe_df = st.session_state['df_pro']
            get_data_indi = convert_df(st.session_state['df_pro'])
            st.download_button("Press to Download", get_data_indi, 'label_intensity_data.csv', "text/csv", key='label_download-get_data') 
            st.session_state['area_thres_x'] = area_thres_x
        else:
            st.session_state['area_thres_x'] = area_thres_x
                 
            data = list(np.unique(label_list_pg_2))        
            st.session_state['df_pro'] = pd.DataFrame(data, columns=['label'])
            col_arr = []
            props_pro = get_intensity(background_corr_pg_2[:, :, :, 0], [label_fin] * raw_img_ani_pg_2.shape[0])  
            props_pro = pd.DataFrame(props_pro).T
            props_pro['label'] = data

            for frames_pro in range(0,raw_img_ani_pg_2.shape[0]):
                col = []
                label_array = props_pro['label']
                intensity_im = background_corr_pg_2[frames_pro][:,:,0]
                #col_arr.append(intensity_im)                        
                for lab in label_array:
                    mask_label = label_fin == lab
                    #st.write(mask_label)
                    intensity_values = intensity_im[mask_label]
                    col.append(intensity_values)
                
                col_arr.append(np.array(col, dtype=object))
                df_single = props_pro
                #df_single['area'] = df_single[df_single['area']>df_single['intensity_mean'].mean()]['area']
                df_single.rename(columns = {frames_pro : f'intensity_mean_{frames_pro}'}, inplace=True)
                df_single[f'intensity_mean_{frames_pro}'] = np.round(df_single[f'intensity_mean_{frames_pro}'],3)
    
            st.session_state['df_pro'] = pd.merge(st.session_state['df_pro'], df_single, on = 'label', how = 'outer')                                              

            ######## #################  ################# ###############Interactive table################################################################

            for frame_col in range(0, raw_img_ani_pg_2.shape[0]):
                
                pixel_counts = []
                for label_val in st.session_state['df_pro']['label']:
                    intensity_image = col_arr[frame_col][label_val-1]
                    count = np.sum(np.greater(intensity_image, st.session_state['area_thres_x']*np.amax(raw_img_ani_pg_2[frame_col]))) #df_pro[f'intensity_mean_{frames_pro}'].mean()))
                    pixel_counts.append(np.float64(count))
                #st.write(type(np.amax(raw_image_ani[frame_col])))
                pixel_var = f'Bright_pixel_area_{frame_col}'
                #df_pro[pixel_var] = pixel_counts
                pixel_counts_df = pd.DataFrame(pixel_counts,columns = [pixel_var],dtype = np.float64)
                st.session_state['df_pro'] = pd.concat((st.session_state['df_pro'], pixel_counts_df),axis=1)   

            st.dataframe(st.session_state['df_pro'], 1000, 200)
            dataframe_df = st.session_state['df_pro']
            get_data_indi = convert_df(st.session_state['df_pro'])
            st.download_button("Press to Download", get_data_indi, 'label_intensity_data.csv', "text/csv", key='label_download-get_data_st') 
    
    st.write('*_Select label(s) to explore_*') 
    area_columns_to_drop = dataframe_df.columns[dataframe_df.columns.str.contains('Bright_pixel_area')]
    dataframe_df_pro = dataframe_df.drop(columns=area_columns_to_drop)
    gb = GridOptionsBuilder.from_dataframe(dataframe_df_pro)                       
    gb.configure_pagination(paginationAutoPageSize=True) #Add pagination
    gb.configure_side_bar() #Add a sidebar
    #gb.configure_selection('multiple', use_checkbox=True, groupSelectsChildren="Group checkbox select children") #Enable multi-row selection
    gb.configure_selection(selection_mode="multiple", use_checkbox=True, groupSelectsChildren="Group checkbox select children", pre_selected_rows=[]) #list(range(0, len(df_pro))))  #[str(st.session_state.selected_row)]
             
    gridOptions = gb.build()
    gridOptions["columnDefs"][0]["checkboxSelection"]=True
    gridOptions["columnDefs"][0]["headerCheckboxSelection"]=True
    
    grid_response_m = AgGrid(
        dataframe_df_pro,
        gridOptions=gridOptions,
        data_return_mode='AS_INPUT', 
        update_mode=GridUpdateMode.SELECTION_CHANGED,    #'MODEL_CHANGED',
        update_on='MANUAL',
        #data_return_mode=DataReturnMode.FILTERED_AND_SORTED,
        fit_columns_on_grid_load=False,
        theme='alpine', #Add theme color to the table
        enable_enterprise_modules=True,
        height=350, 
        width='100%',
        #reload_data=True,
        key='table_m_key'
    )
    
    data = grid_response_m['data']
    selected_m = grid_response_m['selected_rows'] 

    df_selected = pd.DataFrame(selected_m)
    labels_rgb = np.expand_dims(label_fin, axis=2)
    labels_rgbb_m = cv2.cvtColor(img_as_ubyte(labels_rgb), cv2.COLOR_GRAY2RGB)
    
    if selected_m:
        #st.write(selected_m)
        csv_selected = convert_df(df_selected)           
        st.download_button("Press to Download the Selected Data", csv_selected, 'selected_intensity_data.csv', "text/csv", key='download-selected-csv')
        with st.expander("*_Show the correlation between cells_*"):          
            df_selected_trans_hmap = df_selected.iloc[:,2:].transpose()
            #st.write(df_selected_trans_hmap)
            correlation_matrix = df_selected_trans_hmap.corr(method='pearson')
            selected_labels = list(df_selected['label'])
            roi_labels = [f"ROI number {i+1}" for i in range(len(selected_labels))]
            correlation_matrix.columns = roi_labels
            correlation_matrix.index = roi_labels
            props_centroid = get_centroid(background_corr_pg_2[:, :, :, 0], [label_fin])
            # st.write(props_centroid) 
            centroid_x = []
            centroid_y = []
            for values in props_centroid:
                centroid_0_str = values["centroid-0"]  
                centroid_1_str = values["centroid-1"]
              # Convert the cleaned string to a NumPy array
                if isinstance(centroid_0_str, str):
                    centroid_0 = np.fromstring(centroid_0_str.replace("array(", "").replace(")", ""), sep=',')
                else:
                    centroid_0 = centroid_0_str  # If it's already a numpy array

                if isinstance(centroid_1_str, str):
                    centroid_1 = np.fromstring(centroid_1_str.replace("array(", "").replace(")", ""), sep=',')
                else:
                    centroid_1 = centroid_1_str  # If it's already a numpy array

                centroid_x.append(centroid_0) 
                centroid_y.append(centroid_1)
            centroid_col_x = pd.DataFrame(np.array(centroid_x)).T
            centroid_col_y = pd.DataFrame(np.array(centroid_y)).T
            ROI_centroid_df = pd.DataFrame()
            ROI_centroid_df["ROI Number"] = pd.DataFrame(selected_labels)
            ROI_centroid_df["x"] = centroid_col_x
            ROI_centroid_df["y"] = centroid_col_y

            st.write("ROI Centroid Coordinates")
            st.write(ROI_centroid_df)
            get_data_centroid = convert_df(ROI_centroid_df)
            st.download_button("Press to Download", get_data_centroid, 'ROI_centroid_data.csv', "text/csv", key='label_download-get_centroid_st') 

            st.write("The Correlation Matrix")
            st.write(correlation_matrix)
            get_data_correlation = convert_df(correlation_matrix)
            st.download_button("Press to Download", get_data_correlation, 'ROI_correlation_data.csv', "text/csv", key='label_download-get_correlation_st') 
            fig = px.imshow(correlation_matrix, color_continuous_scale='viridis', text_auto=True)
            fig.update_xaxes(tickvals=list(range(len(selected_labels))), ticktext=selected_labels)
            fig.update_yaxes(tickvals=list(range(len(selected_labels))), ticktext=selected_labels)
            # # Adding title to the heatmap
            # ax_hmap.set_title("Correlation Matrix Heatmap")        
            # # Displaying the heatmap in Streamlit
            st.write("The Correlation Heatmap")
            st.plotly_chart(fig)          
           
            
        #st.write(df_selected)# Loop over the selected indices and draw polygons on the color image
        for i in df_selected['label']:
            # Extract the coordinates of the region boundary
            coords = np.argwhere(label_fin==i)
        
            # Create a polygon from the coordinates
            poly = polygon(coords[:, 0], coords[:, 1])
        
            # Set the color of the polygon to red
            color_poly = (255, 0, 0)
        
            # Color the polygon in the color image
            labels_rgbb_m[poly] = color_poly
        st.image(labels_rgbb_m,use_column_width=True,clamp = True)
        df_selected_1 = df_selected.drop(columns = ['_selectedRowNodeInfo'])
        df_selected = df_selected.drop(columns = ['_selectedRowNodeInfo'])
        df_selected_remove = df_selected_1.drop(columns=df_selected_1.filter(regex='^Bright_pixel_area').columns)
        df_selected_transpose = df_selected_remove.transpose()
        df_selected_transpose.columns = (df_selected_transpose.iloc[0])
        df_selected_transpose = df_selected_transpose.drop(index = ['label'])
        df_selected_transpose['Frames'] = list(range(0,df_selected_transpose.shape[0]))
        #st.dataframe(df_selected_transpose)
        frame_rate = st.number_input("Frame Rate (frames per second/fps)", min_value = 0.1, max_value = 100.0, value = 1.0, step = 0.1, format = "%.1f", help = "Type the values between 0.1 and 100.0 (inclusive). Takes values in steps of 0.1. Default is 1.0")
        df_selected_transpose['Time'] = df_selected_transpose['Frames']/frame_rate
        # create an empty list to store the traces
        traces = []
        
        # loop through each column (excluding the x column)
        for column in df_selected_transpose.columns[:-2]:    
            # create a trace for the current column
            trace = go.Scatter(x=df_selected_transpose['Time'], y=df_selected_transpose[column], name=column)
            # add the trace to the list
            traces.append(trace)
        # create the plot
        fig = go.Figure(data=traces)
        # update the layout
        fig.update_layout(title='Original Intensity Traces', xaxis_title='Time', yaxis_title='Mean Intensity',height=900)
        # display the plot
        st.plotly_chart(fig, use_container_width=True) 
        
        st.write("*_Select the parameters to be applied on all labels_*")
        
        
        bleach_corr_check = st.radio("Select one", ('No bleaching correction', 'Bleaching correction'), help='Analyze the trace as is (No bleaching correction) or fit mono-exponential curves and interpolate to correct for bleaching (Bleaching correction)')
        
        if bleach_corr_check == 'No bleaching correction':
            baseline_peak_selection = st.radio("Select one", ('Static', 'Dynamic'), help='Select "Static" to manually select single values for the baseline, peak and recovery frames; otherwise, select "Dynamic"')
            smooth_plot_x = st.number_input("*_Moving Average Window_*", min_value=1, max_value=5, help = "Adjust to smooth the mean intensity trace below. Moving average of 1 would mean the original 'Mean Intensity' trace")
            if baseline_peak_selection == "Dynamic":            
                
                baseline_smooth_x = st.number_input("*_Choose frame number(s) to average their corresponding intensity values for baseline calculation_*", min_value = 0, max_value = raw_img_ani_pg_2.shape[0]-1, value = 10,  key='smooth_multi_0')
                
                if st.button("Obtain the parameters for selected labels",on_click=callback_movav) or st.session_state.button_clicked_movav:
                    
                    st.warning("The parameters for all labels are obtained using the same set of selections.")
                    df_pro_pixel_remove = df_selected_1.drop(columns=df_selected.filter(regex='^Bright_pixel_area_').columns)
                    #df_pro_pixel_remove = df_pro_pixel_remove.drop(columns=df_pro.filter(regex='^area').columns)
                    new_df_pro_transposed_smooth = df_pro_pixel_remove.transpose()
                    new_df_pro_transposed_smooth.columns = new_df_pro_transposed_smooth.iloc[0]
                    new_df_pro_transposed_smooth.drop(new_df_pro_transposed_smooth.index[0], inplace=True)  
                    
                    
                    #smooth_plot_x = st.slider("*_Moving Average Window_*", min_value=1, max_value=5, help = "Select to smooth the intensity trace. Moving average of 1 would mean the original 'Mean Intensity' trace below", key = 'mov_av')
                    for i in df_selected['label']: 
                        
                        df_pro_transposed_smooth = pd.DataFrame(smooth_plot(new_df_pro_transposed_smooth[i],smooth_plot_x),columns = [f'smooth cell {i}'])
                        new_df_pro_transposed_smooth = pd.concat([new_df_pro_transposed_smooth.reset_index(drop=True), (np.round(df_pro_transposed_smooth[f'smooth cell {i}'],3)).reset_index(drop=True)],axis=1)
                        new_df_missing_values = pd.isna(new_df_pro_transposed_smooth[f"smooth cell {i}"])
                        new_df_pro_transposed_smooth.loc[new_df_missing_values, f'smooth cell {i}'] = new_df_pro_transposed_smooth.loc[new_df_missing_values, i]                               
                        
                        #st.write(new_df_pro_transposed)
                    new_df_pro_transposed_smooth['Frame'] = pd.DataFrame(list(range(0, df_selected.shape[1])))
                    new_df_pro_transposed_smooth = new_df_pro_transposed_smooth.iloc[:, [new_df_pro_transposed_smooth.shape[1] - 1] + list(range(new_df_pro_transposed_smooth.shape[1] - 1))]
                    new_df_pro_transposed_smooth['Time'] = new_df_pro_transposed_smooth['Frame']/frame_rate                    

                    nested_dict_final = {}           
                    nested_dict_pro = {'Label':[], "Number of Events":[], "Rise time":[], "Rise Rate":[], "Decay time":[], "Decay Rate":[], "Duration":[], "Amplitude":[]}
    
                    for i in df_selected['label']:
                        
                        baseline_each = new_df_pro_transposed_smooth.loc[(new_df_pro_transposed_smooth['Frame'] >= 0) & (new_df_pro_transposed_smooth['Frame'] <= baseline_smooth_x), f'smooth cell {i}'].mean()
                        baseline_mean_each = new_df_pro_transposed_smooth.loc[(new_df_pro_transposed_smooth['Frame'] >= 0) & (new_df_pro_transposed_smooth['Frame'] <= baseline_smooth_x), float(f'{i}.0')].mean()
                        new_df_pro_transposed_smooth[float(f'{i}.0')] = new_df_pro_transposed_smooth[float(f'{i}.0')]/baseline_mean_each
                        
                        #st.write(baseline_each)
                        new_df_pro_transposed_smooth[f'smooth cell {i}'] = new_df_pro_transposed_smooth[f'smooth cell {i}']/baseline_each
                        baseline_each = baseline_each/baseline_each                    
                        new_df_pro_transposed_smooth[f'delta_f/f_0_{i}'] = (new_df_pro_transposed_smooth[f'smooth cell {i}'] - baseline_each)/baseline_each 
                        keyval = {}
                        amp_keyval = {}
                        prev_intensity = 0
                        flag = 1
                        for frame_key, intensity_val in enumerate(new_df_pro_transposed_smooth[f'smooth cell {i}']):
                            if prev_intensity == 0 and intensity_val > baseline_each:
                                continue
                            elif intensity_val >= baseline_each:
                                keyval[frame_key] = intensity_val
                                break
                            else:
                                if frame_key==len(new_df_pro_transposed_smooth.index)-1:
                                    flag = 0
                                else:
                                    prev_intensity = intensity_val
                                    continue
                        if flag==0:
                            prev_intensity = 0
                            continue
                        
                        first_key = frame_key
                        first_intensity = keyval[frame_key]
                        
                        prev_intensity = keyval[frame_key]
                        for frame_key_2, intensity_val_2 in enumerate(new_df_pro_transposed_smooth[f'smooth cell {i}']):                               
                            if frame_key_2 <= frame_key:
                                continue
                            elif frame_key_2 > frame_key:
                                if intensity_val_2 >= prev_intensity:
                                    if intensity_val_2 < baseline_each:
                                        frame_key = frame_key_2
                                        continue
                                    elif intensity_val_2 >= baseline_each:
                                        if prev_intensity < baseline_each:
                                            first_key = frame_key_2
                                            first_intensity = intensity_val_2
                                            keyval[first_key] = first_intensity
                                            frame_key = frame_key_2
                                            prev_intensity = intensity_val_2
                                        else:
                                            frame_key = frame_key_2
                                            prev_intensity = intensity_val_2
                                        
                
                                elif intensity_val_2 < prev_intensity:
                                    if intensity_val_2 > baseline_each:
                                        frame_key = frame_key_2                                         
                                    elif intensity_val_2 <= baseline_each:
                                        if prev_intensity <= baseline_each:
                                            frame_key = frame_key_2
                                            continue
                                        else:
                                            keyval[frame_key_2] = intensity_val_2
                                            frame_key = frame_key_2
                                            #start_key = plot_df.query(f'"Smoothed Mean Intensity" == {prev_intensity}')['Frame']
                                            amp_key_vals = new_df_pro_transposed_smooth[new_df_pro_transposed_smooth[f'smooth cell {i}']==prev_intensity]['Frame']
                                            amp_key_vals = amp_key_vals[amp_key_vals>=first_key].iloc[0]
                                            amp_key = str(amp_key_vals)
                                            #amp_key = str(new_df_pro_transposed_smooth[new_df_pro_transposed_smooth[f'smooth cell {i}']==prev_intensity]['Frame'].iloc[0])
                                            amplitude = prev_intensity - baseline_each
                                            keyval[amp_key] = prev_intensity
                                            prev_intensity = intensity_val_2
                                            if (first_key == int(amp_key)): #or (int(amp_key) == frame_key): 
                                                first_key = int(amp_key)-1
                                                amp_keyval[f"{first_key}-{amp_key}-{frame_key}"] = amplitude
                                            else:
                                                amp_keyval[f"{first_key}-{amp_key}-{frame_key}"] = amplitude                
                        
                        
                        max_df_value = new_df_pro_transposed_smooth[f'smooth cell {i}'].max()

                        #####test by setting a some equal high values#########plot_df.loc[plot_df['Frame'] == 39, 'Smoothed Mean Intensity'] = max_df_value ##plot_df.loc[plot_df['Frame'] == 69, 'Smoothed Mean Intensity'] = baseline_each
                        count_max = new_df_pro_transposed_smooth[f'smooth cell {i}'].eq(max_df_value).sum()
                        max_frame = new_df_pro_transposed_smooth.loc[new_df_pro_transposed_smooth[f'smooth cell {i}'] == max_df_value, 'Frame']
                        decay_df = pd.DataFrame()
                        rise_df = pd.DataFrame()
                        if ((new_df_pro_transposed_smooth.loc[new_df_pro_transposed_smooth["Frame"].gt(max(max_frame)), f'smooth cell {i}']).gt(baseline_each)).all(): ##trace crosses baseline but never comes back
                            #nested_dict_pro = {'Label':[], "Number of Events":[], "Rise time":[], "Rise Rate":[], "Decay time":[], "Decay Rate":[], "Duration":[], "Amplitude":[]}
                           if count_max == 1:
                            rise_df['Rise intensity'] = new_df_pro_transposed_smooth.loc[(new_df_pro_transposed_smooth[f'smooth cell {i}'] <= max_df_value) & (new_df_pro_transposed_smooth[f'smooth cell {i}'] >= baseline_each) & (new_df_pro_transposed_smooth['Frame'] <= max(max_frame)) , f'smooth cell {i}']
                            rise_df['Frame'] = rise_df.index
                            rise_df = rise_df[rise_df.columns[::-1]]
                            missing_value_rise_df = (rise_df.loc[rise_df['Frame'].diff() > 1, 'Frame'].max())-1
                            #st.write(~rise_df['Rise intensity'].isin([baseline_each]).any())
                            # if ~decay_df['Decay intensity'].isin([baseline_each]).any():
                            #     new_row_decay = {'Frame':  missing_value_df, 'Decay intensity': baseline_each}
                            #     decay_df.loc[len(decay_df)] = new_row_decay
                            # if ~rise_df['Rise intensity'].isin([baseline_each]).any():
                            #     new_row_rise = {'Frame':  missing_value_rise_df, 'Rise intensity': baseline_each}
                            #     rise_df.loc[missing_value_rise_df] = new_row_rise
                            
                            #decay_df.loc[decay_df['Frame'] == missing_value_df, 'Decay intensity'] == baseline_each
                            #st.write(missing_value_df)
                                
                            if not pd.isna(missing_value_rise_df):
                                #st.write('here')
                                rise_df = rise_df.loc[rise_df['Frame'] >= missing_value_rise_df]
                            else:
                                if (rise_df['Rise intensity'] == baseline_each).any():
                                    #st.write(rise_df)
                                    baseline_frame = max(rise_df.loc[rise_df['Rise intensity'] == baseline_each, 'Frame'])
                                    rise_df = rise_df.loc[(rise_df['Rise intensity'] >= baseline_each) & (rise_df['Frame'] >= baseline_frame)]  
                                else:
                                    rise_df = rise_df   
                            
                            #st.write(missing_value_df)
                            
                            if count_max > 1: 
                                                        
                                rise_df['Rise intensity'] = new_df_pro_transposed_smooth.loc[(new_df_pro_transposed_smooth[f'smooth cell {i}'] <= max_df_value) & (new_df_pro_transposed_smooth[f'smooth cell {i}'] >= baseline_each) & (new_df_pro_transposed_smooth['Frame'] <= min(max_frame)) , f'smooth cell {i}']
                                first_index = rise_df.loc[rise_df['Rise intensity'] == max_df_value].index[-1]                    
                                #rise_df.loc[first_index, 'Rise intensity'] *= 1.01                        
                                rise_df['Frame'] = rise_df.index
                                rise_df = rise_df[rise_df.columns[::-1]]
                                #st.write(decay_df)
                                
                                missing_value_rise_df = (rise_df.loc[rise_df['Frame'].diff() > 1, 'Frame'].max())-1
                                #st.write(np.any(rise_df['Rise intensity']) != baseline_each)
                                # if ~decay_df['Decay intensity'].isin([baseline_each]).any():
                                #     if missing_value_df is not None:
                                #         new_row_decay = {'Frame':  missing_value_df, 'Decay intensity': baseline_each}
                                #         decay_df.loc[len(decay_df)] = new_row_decay
                                # if ~rise_df['Rise intensity'].isin([baseline_each]).any():
                                #     if missing_value_rise_df is not None:
                                #         new_row_rise = {'Frame':  missing_value_rise_df, 'Rise intensity': baseline_each}
                                #         rise_df.loc[missing_value_rise_df] = new_row_rise
                                #decay_df.loc[decay_df['Frame'] == missing_value_df, 'Decay intensity'] == baseline_each
                                #st.write(missing_value_rise_df)
                                    
                                if not pd.isna(missing_value_rise_df):
                                    #st.write('here')
                                    rise_df = rise_df.loc[rise_df['Frame'] >= missing_value_rise_df]
                                else:
                                    if (rise_df['Rise intensity'] == baseline_each).any():
                                        #st.write(rise_df)
                                        baseline_frame = max(rise_df.loc[rise_df['Rise intensity'] == baseline_each, 'Frame'])
                                        rise_df = rise_df.loc[(rise_df['Rise intensity'] >= baseline_each) & (rise_df['Frame'] >= baseline_frame)]  
                                    else:
                                        rise_df = rise_df          
                                           
                            a_est_rise = rise_df['Rise intensity'].iloc[-1]
                            b_est_rise = find_b_est_rise(np.array(rise_df['Frame']), np.array(rise_df['Rise intensity']))
                            #bounds = ([0, 0], [100, 100])
                            
                            popt_decay, pcov_decay = None, None                        
                            
                            try:
                                popt_rise, pcov_rise = curve_fit(mono_exp_rise, rise_df['Frame'], rise_df['Rise intensity'], p0=[a_est_rise,b_est_rise])
                                
                            except (TypeError, RuntimeError) as e:
                                error_message = str(e)
                                if error_message == "Optimal parameters not found: Number of calls to function has reached maxfev = 600":
                                    popt_rise, pcov_rise = None, None
                                    
                                # Replace the error with a warning message
                                else:                           
                                    warning_message = "Fitting cannot be performed"
                                    warnings.warn(warning_message, category=UserWarning)
                                    popt_rise, pcov_rise = None, None
                                    #bounds = ([0, 0], [100, 100])
                                    #st.write(a_est)
                            else:
                                popt_rise, pcov_rise = curve_fit(mono_exp_rise, rise_df['Frame'], rise_df['Rise intensity'], p0=[a_est_rise,b_est_rise])
                                rise_curve_exp = np.round((mono_exp_rise(rise_df['Frame'], *popt_rise)),3)  
                                
                            signal_rise = (max(max_frame) - rise_df['Frame'].iloc[0])/frame_rate
                            amplitude_each = max_df_value - baseline_each
                            if (pcov_decay is None) and (popt_decay is None):
                                nested_dict_pro["Label"].append(i)
                                nested_dict_pro["Number of Events"].append(None)
                                nested_dict_pro["Rise time"].append(signal_rise)
                                nested_dict_pro["Decay time"].append(None)
                                nested_dict_pro["Duration"].append(None)
                                nested_dict_pro["Amplitude"].append(amplitude_each) 
                                if popt_rise is not None:
                                    rise_rate = np.round(popt_rise[1],4)
                                    nested_dict_pro["Rise Rate"].append(rise_rate)
                                else:
                                    nested_dict_pro["Rise Rate"].append(None)
                                nested_dict_pro["Decay Rate"].append(None)
                        else:
                            
                            if count_max == 1:
                                rise_df['Rise intensity'] = new_df_pro_transposed_smooth.loc[(new_df_pro_transposed_smooth[f'smooth cell {i}'] <= max_df_value) & (new_df_pro_transposed_smooth[f'smooth cell {i}'] >= baseline_each) & (new_df_pro_transposed_smooth['Frame'] <= min(max_frame)) , f'smooth cell {i}']
                                decay_df['Decay intensity'] = new_df_pro_transposed_smooth.loc[(new_df_pro_transposed_smooth[f'smooth cell {i}'] <= max_df_value) & (new_df_pro_transposed_smooth[f'smooth cell {i}'] >= baseline_each) & (new_df_pro_transposed_smooth['Frame'] >= max(max_frame)) , f'smooth cell {i}']
                                decay_df['Frame'] = decay_df.index
                                rise_df['Frame'] = rise_df.index
                                decay_df = decay_df[decay_df.columns[::-1]]
                                rise_df = rise_df[rise_df.columns[::-1]]
                                test_missing_value_df = next((decay_df['Frame'].iloc[i] + 1 for i in range(len(decay_df['Frame'])-1) if decay_df['Frame'].iloc[i+1] - decay_df['Frame'].iloc[i] > 1), None)
                                if test_missing_value_df is None:
                                    missing_value_df = None
                                else:
                                    missing_value_df = test_missing_value_df - 1 
                                missing_value_rise_df = (rise_df.loc[rise_df['Frame'].diff() > 1, 'Frame'].max())-1
                                #st.write(~rise_df['Rise intensity'].isin([baseline_each]).any())
                                # if ~decay_df['Decay intensity'].isin([baseline_each]).any():
                                #     new_row_decay = {'Frame':  missing_value_df, 'Decay intensity': baseline_each}
                                #     decay_df.loc[len(decay_df)] = new_row_decay
                                # if ~rise_df['Rise intensity'].isin([baseline_each]).any():
                                #     new_row_rise = {'Frame':  missing_value_rise_df, 'Rise intensity': baseline_each}
                                #     rise_df.loc[missing_value_rise_df] = new_row_rise
                                
                                #decay_df.loc[decay_df['Frame'] == missing_value_df, 'Decay intensity'] == baseline_each
                                #st.write(missing_value_df)
                                if not pd.isna(missing_value_df): #there is a missing value
                                    #st.write('here')
                                    decay_df = decay_df.loc[decay_df['Frame'] <= missing_value_df]
                                 
                                else:
                                    if (decay_df['Decay intensity'] == baseline_each).any():
                                        baseline_frame = max(decay_df.loc[decay_df['Decay intensity'] == baseline_each, 'Frame'])
                                        decay_df = decay_df.loc[(decay_df['Decay intensity'] >= baseline_each) & (decay_df['Frame'] <= baseline_frame)]  
                                    else:
                                        decay_df = decay_df
                                    
                                if not pd.isna(missing_value_rise_df):
                                    #st.write('here')
                                    rise_df = rise_df.loc[rise_df['Frame'] >= missing_value_rise_df]
                                else:
                                    if (rise_df['Rise intensity'] == baseline_each).any():
                                        #st.write(rise_df)
                                        baseline_frame = max(rise_df.loc[rise_df['Rise intensity'] == baseline_each, 'Frame'])
                                        rise_df = rise_df.loc[(rise_df['Rise intensity'] >= baseline_each) & (rise_df['Frame'] >= baseline_frame)]  
                                    else:
                                        rise_df = rise_df
                                #st.write(rise_df)
                                #st.write(missing_value_df)
                                
                            if count_max > 1: 
                                avg_frame = int(np.floor(max_frame.mean()))                                
                                decay_df['Decay intensity'] = new_df_pro_transposed_smooth.loc[(new_df_pro_transposed_smooth[f'smooth cell {i}'] <= max_df_value) & (new_df_pro_transposed_smooth[f'smooth cell {i}'] >= baseline_each) & (new_df_pro_transposed_smooth['Frame'] >= max(max_frame)) , f'smooth cell {i}']
                                last_index = decay_df.loc[decay_df['Decay intensity'] == max_df_value].index[-1]
                                rise_df['Rise intensity'] = new_df_pro_transposed_smooth.loc[(new_df_pro_transposed_smooth[f'smooth cell {i}'] <= max_df_value) & (new_df_pro_transposed_smooth[f'smooth cell {i}'] >= baseline_each) & (new_df_pro_transposed_smooth['Frame'] <= min(max_frame)) , f'smooth cell {i}']
                                first_index = rise_df.loc[rise_df['Rise intensity'] == max_df_value].index[0]                 
                                #decay_df.loc[last_index, 'Decay intensity'] *= 1.01
                                #rise_df.loc[first_index, 'Rise intensity'] *= 1.01
                                decay_df['Frame'] = decay_df.index
                                rise_df['Frame'] = rise_df.index
                                decay_df = decay_df[decay_df.columns[::-1]]
                                rise_df = rise_df[rise_df.columns[::-1]]
                                #st.write(decay_df)
                                test_missing_value_df = next((decay_df['Frame'].iloc[i] + 1 for i in range(len(decay_df['Frame'])-1) if decay_df['Frame'].iloc[i+1] - decay_df['Frame'].iloc[i] > 1), None)
                                if test_missing_value_df is None:
                                    missing_value_df = None
                                else:
                                    missing_value_df = test_missing_value_df - 1                         
                                missing_value_rise_df = (rise_df.loc[rise_df['Frame'].diff() > 1, 'Frame'].max())-1
                                #st.write(np.any(rise_df['Rise intensity']) != baseline_each)
                                # if ~decay_df['Decay intensity'].isin([baseline_each]).any():
                                #     new_row_decay = {'Frame':  missing_value_df, 'Decay intensity': baseline_each}
                                #     decay_df.loc[len(decay_df)] = new_row_decay
                                # if ~rise_df['Rise intensity'].isin([baseline_each]).any():
                                #     new_row_rise = {'Frame':  missing_value_rise_df, 'Rise intensity': baseline_each}
                                #     rise_df.loc[missing_value_rise_df] = new_row_rise
                                #decay_df.loc[decay_df['Frame'] == missing_value_df, 'Decay intensity'] == baseline_each
                                #st.write(missing_value_rise_df)
                                if not pd.isna(missing_value_df):
                                    #st.write('here')
                                    decay_df = decay_df.loc[decay_df['Frame'] <= missing_value_df]
                                else:
                                    if (decay_df['Decay intensity'] == baseline_each).any():
                                        baseline_frame = max(decay_df.loc[decay_df['Decay intensity'] == baseline_each, 'Frame'])
                                        decay_df = decay_df.loc[(decay_df['Decay intensity'] >= baseline_each) & (decay_df['Frame'] <= baseline_frame)]  
                                    else:
                                        decay_df = decay_df
                                    
                                if not pd.isna(missing_value_rise_df):
                                    #st.write('here')
                                    rise_df = rise_df.loc[rise_df['Frame'] >= missing_value_rise_df]
                                else:
                                    if (rise_df['Rise intensity'] == baseline_each).any():
                                        #st.write(rise_df)
                                        baseline_frame = max(rise_df.loc[rise_df['Rise intensity'] == baseline_each, 'Frame'])
                                        rise_df = rise_df.loc[(rise_df['Rise intensity'] >= baseline_each) & (rise_df['Frame'] >= baseline_frame)]  
                                    else:
                                        rise_df = rise_df             
                                #st.write(rise_df)
                            
                            a_est = decay_df['Decay intensity'].iloc[0]
                            b_est = find_b_est_decay(np.array(decay_df['Frame']), np.array(decay_df['Decay intensity']))
                            a_est_rise = rise_df['Rise intensity'].iloc[-1]
                            b_est_rise = find_b_est_rise(np.array(rise_df['Frame']), np.array(rise_df['Rise intensity']))
                            #bounds = ([0, 0], [100, 100])
                            #st.write(a_est)
                            try:
                                popt_decay, pcov_decay = curve_fit(mono_exp_decay, decay_df['Frame'], decay_df['Decay intensity'], p0=[a_est,b_est])
                                
                            except (TypeError, RuntimeError) as e:
                                error_message = str(e)
                                if error_message == "Optimal parameters not found: Number of calls to function has reached maxfev = 600":
                                    # Handle the error and continue to the next iteration
                                    continue
                                #st.write("here")
                                # Replace the error with a warning message
                                else:
                                    warning_message = "Fitting cannot be performed"
                                    warnings.warn(warning_message, category=UserWarning)
                                    popt_decay, pcov_decay = None, None
                            else: 
                                popt_decay, pcov_decay = curve_fit(mono_exp_decay, decay_df['Frame'], decay_df['Decay intensity'], p0=[a_est,b_est])
                                decay_curve_exp = mono_exp_decay(decay_df['Frame'], *popt_decay)
    
                                #st.write(popt_decay)
                            try:
                                popt_rise, pcov_rise = curve_fit(mono_exp_rise, rise_df['Frame'], rise_df['Rise intensity'], p0=[a_est_rise,b_est_rise])
                                
                            except (TypeError, RuntimeError) as e:
                                error_message = str(e)
                                if error_message == "Optimal parameters not found: Number of calls to function has reached maxfev = 600":
                                    continue
                                # Replace the error with a warning message
                                else:                           
                                    warning_message = "Fitting cannot be performed"
                                    warnings.warn(warning_message, category=UserWarning)
                                    popt_rise, pcov_rise = None, None
                                    #bounds = ([0, 0], [100, 100])
                                    #st.write(a_est)
                            else:
                                popt_rise, pcov_rise = curve_fit(mono_exp_rise, rise_df['Frame'], rise_df['Rise intensity'], p0=[a_est_rise,b_est_rise])
                                rise_curve_exp = np.round((mono_exp_rise(rise_df['Frame'], *popt_rise)),3)                
                                #st.write(popt_decay)
                                #st.write(popt_rise)
                                
                                
                                # st.write(i)
                                # st.write(nested_dict_final)
                            count_items = 0
                            for item in amp_keyval.items():
                                #st.write(item[0].split('-')) 
                                if len(item[0].split('-'))==3:
                                    count_items += 1
                                    signal_start_frame = item[0].split('-')[0]
                                    #st.write(f"The signal start frame is {int(signal_start_frame)}")
                                    peak_frame = item[0].split('-')[1]
                                    #st.write(f"The peak frame is {int(peak_frame)}")
                                    signal_decay_frame = item[0].split('-')[2]
                                    #st.write(f"The signal decay frame is {int(signal_decay_frame)}")
                                    event_num = count_items
                                    amplitude_each = item[1]
                                    signal_rise = (int(peak_frame)-int(signal_start_frame))/frame_rate
                                    signal_decay = (int(signal_decay_frame)-int(peak_frame))/frame_rate
                                    signal_duration = (int(signal_decay_frame)-int(signal_start_frame))/frame_rate
        
                                    if (popt_rise is not None) and (popt_decay is not None):
                                        nested_dict_pro["Label"].append(i)
                                        nested_dict_pro["Number of Events"].append(event_num)
                                        nested_dict_pro["Rise time"].append(signal_rise)
                                        nested_dict_pro["Decay time"].append(signal_decay)
                                        nested_dict_pro["Duration"].append(signal_duration)
                                        nested_dict_pro["Amplitude"].append(amplitude_each) 
                                        rise_rate = np.round(popt_rise[1],4)
                                        nested_dict_pro["Rise Rate"].append(rise_rate)
                                        decay_rate = np.round(popt_decay[1],4)
                                        nested_dict_pro["Decay Rate"].append(decay_rate)
                    
                                        
                    #st.dataframe(new_df_pro_transposed_smooth, 1000,200)
                    nested_dict_final = nested_dict_pro.copy()  
                    st.write(new_df_pro_transposed_smooth)
                    multi_csv = convert_df(new_df_pro_transposed_smooth)           
                    st.download_button("Press to Download",  multi_csv, 'multi_cell_data.csv', "text/csv", key='download_multi_-csv')                
                    #st.write(nested_dict_final)
                    nested_dict_final = (pd.DataFrame.from_dict(nested_dict_final))
                    traces_smooth = []                    
                    column_new_df = new_df_pro_transposed_smooth.columns              
                    for smooth_column in column_new_df:    
                        if "smooth cell" in str(smooth_column):
                            # create a trace for the current column
                            trace_smooth = go.Scatter(x=new_df_pro_transposed_smooth['Time'], y=new_df_pro_transposed_smooth[smooth_column], name=smooth_column)
                            # add the trace to the list
                            traces_smooth.append(trace_smooth)
                    # create the plot
                    fig_smooth = go.Figure(data=traces_smooth)
                    # update the layout
                    fig_smooth.update_layout(title='Normalized Intensity Traces', xaxis_title='Time', yaxis_title='Normalized Intensity',height=900)
                    # display the plot
                    st.plotly_chart(fig_smooth, use_container_width=True)                      
                    
                    if nested_dict_final.empty:
                        pass
                    else:                              
                        st.subheader("**_Parameters for selected labels_**")
                        col_7, col_8 = st.columns(2)
                        
                        with col_7: 
                            nested_dict_final = nested_dict_final[nested_dict_final.groupby('Label')['Amplitude'].transform(max) == nested_dict_final['Amplitude']]
                            nested_dict_final['Number of Events'] = nested_dict_final.groupby('Label')['Number of Events'].transform('count')
    
                            st.write(nested_dict_final)  
                            all_csv = convert_df(nested_dict_final)           
                            st.download_button("Press to Download", all_csv, 'all_data.csv', "text/csv", key='all_download-csv')
                        with col_8:
                            average_rise_time = np.round(nested_dict_final['Rise time'].mean(),4)
                            st.write(f"The average rise time based on selected labels across all frames is {average_rise_time} s")
                            average_rise_rate = np.round(nested_dict_final['Rise Rate'].mean(),4)
                            st.write(f"The average rise rate based on selected labels across all frames is {average_rise_rate} per s")
                            average_decay_time = np.round(nested_dict_final['Decay time'].mean(),4)
                            st.write(f"The average decay time based on selected labels across all frames is {average_decay_time} s")
                            average_decay_rate = np.round(nested_dict_final['Decay Rate'].mean(),4)
                            st.write(f"The average decay rate based on selected labels across all frames is {average_decay_rate} per s")
                            average_duration = np.round(nested_dict_final['Duration'].mean(),4)
                            st.write(f"The average duration based on selected labels across all frames is {average_duration} s")
                            average_amplitude = np.round(nested_dict_final['Amplitude'].mean(),4)
                            st.write(f"The average amplitude based on selected labels across all frames is {average_amplitude}")
                        
                        nested_dict_final['Amplitude'] = np.round(nested_dict_final['Amplitude'], 2)    
                        nested_dict_final['Duration'] = np.round(nested_dict_final['Duration'], 2)   
                        nested_dict_final['Decay time'] = np.round(nested_dict_final['Decay time'], 2)  
                        nested_dict_final['Rise time'] = np.round(nested_dict_final['Rise time'], 2) 
                        nested_dict_final['Rise Rate'] = np.round(nested_dict_final['Rise Rate'], 2)
                        nested_dict_final['Decay Rate'] = np.round(nested_dict_final['Decay Rate'], 2)
                        
                        exclude_columns = ['Label', 'Number of Events']
                        columns_to_plot = [col for col in nested_dict_final.columns if col not in exclude_columns]
                        
                        fig = make_subplots(rows=3, cols=2, subplot_titles = ["A", "B", "C", "D", "E", "F"])                      
                        for i, colu in enumerate(columns_to_plot):
                            row = i // 2 + 1
                            col = i % 2 + 1                            
                            fig.add_trace(go.Histogram(x=nested_dict_final[colu], name=colu, nbinsx=20, marker_line_color='black', marker_line_width=1), row=row, col=col)                                   
                        fig.update_layout(title="Histograms",height=1000, width=800, showlegend=False)
                        fig.update_xaxes(title_text="Rise time (s)", row=1, col=1)
                        fig.update_xaxes(title_text="Rise Rate (s⁻¹)", row=1, col=2)
                        fig.update_xaxes(title_text="Decay time (s)", row=2, col=1)
                        fig.update_xaxes(title_text="Decay Rate (s⁻¹)", row=2, col=2)
                        fig.update_xaxes(title_text="Duration (s)", row=3, col=1)
                        fig.update_xaxes(title_text="Amplitude", row=3, col=2)
                        fig.update_yaxes(title_text="Number of selected cells", row=1, col=1)
                        fig.update_yaxes(title_text="Number of selected cells", row=2, col=1)
                        fig.update_yaxes(title_text="Number of selected cells", row=3, col=1)
                        st.plotly_chart(fig)                

                        st.warning('Navigating to another page from the sidebar will remove all selections from the current page')

            if baseline_peak_selection == "Static": 
                baseline_recovery_frame_input = st.radio("Select one", ('Single Frame Value', 'Average Frame Value'), help='Baseline value based on a single frame, or on multiple frames')
                if baseline_recovery_frame_input ==   'Single Frame Value':                                     
                    baseline__frame_static = st.number_input("Baseline Intensity Frame number",  min_value=0, max_value=raw_img_ani_pg_2.shape[0]-1)
                elif baseline_recovery_frame_input ==   'Average Frame Value': 
                    baseline_smooth_x = st.number_input("*_Choose frame number(s) to average their corresponding intensity values for baseline calculation_*", min_value = 0, max_value = raw_img_ani_pg_2.shape[0]-1, value = 10,  key='smooth')
                    baseline__frame_static = int(sum(range(baseline_smooth_x + 1)) / (baseline_smooth_x + 1))
                df_pro_pixel_remove = df_selected_1.drop(columns=df_selected.filter(regex='^Bright_pixel_area_').columns)
                #df_pro_pixel_remove = df_pro_pixel_remove.drop(columns=df_pro.filter(regex='^area').columns)
                new_df_pro_transposed_smooth = df_pro_pixel_remove.transpose()
                new_df_pro_transposed_smooth.columns = new_df_pro_transposed_smooth.iloc[0]
                new_df_pro_transposed_smooth.drop(new_df_pro_transposed_smooth.index[0], inplace=True)      
                peak__frame_static = st.number_input("Peak Intensity Frame number",  min_value=0, max_value=raw_img_ani_pg_2.shape[0]-1, value = int((raw_img_ani_pg_2.shape[0])/2)) 
                recovery_baseline__frame_static = st.number_input("Recovery Intensity Frame number",  min_value=0, max_value=raw_img_ani_pg_2.shape[0]-1, value = int(raw_img_ani_pg_2.shape[0])-1)                  
                for i in df_selected['label']: 
                        
                    df_pro_transposed_smooth = pd.DataFrame(smooth_plot(new_df_pro_transposed_smooth[i],smooth_plot_x),columns = [f'smooth cell {i}'])
                    new_df_pro_transposed_smooth = pd.concat([new_df_pro_transposed_smooth.reset_index(drop=True), (np.round(df_pro_transposed_smooth[f'smooth cell {i}'],3)).reset_index(drop=True)],axis=1)
                    new_df_missing_values = pd.isna(new_df_pro_transposed_smooth[f"smooth cell {i}"])
                    new_df_pro_transposed_smooth.loc[new_df_missing_values, f'smooth cell {i}'] = new_df_pro_transposed_smooth.loc[new_df_missing_values, i]                               
                        
                    #st.write(new_df_pro_transposed)
                new_df_pro_transposed_smooth['Frame'] = pd.DataFrame(list(range(0, df_selected.shape[1])))
                new_df_pro_transposed_smooth = new_df_pro_transposed_smooth.iloc[:, [new_df_pro_transposed_smooth.shape[1] - 1] + list(range(new_df_pro_transposed_smooth.shape[1] - 1))]
                new_df_pro_transposed_smooth['Time'] = new_df_pro_transposed_smooth['Frame']/frame_rate
                
                if st.button("Obtain the parameters for selected labels",on_click=callback_movav_sta):       
                    st.warning("The parameters for all labels are obtained using the same set of selections.")                   
                    #st.write(new_df_pro_transposed)
          
                    nested_dict_final = {}           
                    nested_dict_pro = {'Label':[], "Number of Events":[], "Rise time":[], "Rise Rate":[], "Decay time":[], "Decay Rate":[], "Duration":[], "Amplitude":[]}
        
                    if baseline_recovery_frame_input ==   'Single Frame Value': 
                        for i in df_selected['label']:                                     
                            filtered_baseline_each = new_df_pro_transposed_smooth.query("Frame == @baseline__frame_static")
                            baseline_each = filtered_baseline_each[f'smooth cell {i}'].iloc[0]
                            filtered_baseline_mean_each = new_df_pro_transposed_smooth.query("Frame == @baseline__frame_static")
                            baseline_mean_each = filtered_baseline_mean_each[float(f'{i}.0')].iloc[0]  
                            new_df_pro_transposed_smooth[f'smooth cell {i}'] = new_df_pro_transposed_smooth[f'smooth cell {i}']/baseline_each
                            baseline_each = baseline_each/baseline_each                    
                            new_df_pro_transposed_smooth[f'delta_f/f_0_{i}'] = (new_df_pro_transposed_smooth[f'smooth cell {i}'] - baseline_each)/baseline_each 
                            filtered_peak_each = new_df_pro_transposed_smooth.query("Frame == @peak__frame_static")
                            max_df_value = filtered_peak_each[f'smooth cell {i}'].iloc[0]
                            rise_df = new_df_pro_transposed_smooth[(new_df_pro_transposed_smooth['Frame'] >= baseline__frame_static) & (new_df_pro_transposed_smooth['Frame'] <= peak__frame_static)]
                            decay_df = new_df_pro_transposed_smooth[(new_df_pro_transposed_smooth['Frame'] >= peak__frame_static) & (new_df_pro_transposed_smooth['Frame'] <= recovery_baseline__frame_static)]
                            decay_df = decay_df[['Frame', f'smooth cell {i}']]
                            decay_df.rename(columns={f'smooth cell {i}': 'Decay intensity'}, inplace=True)
                            rise_df = rise_df[['Frame', f'smooth cell {i}']]
                            rise_df.rename(columns={f'smooth cell {i}': 'Rise intensity'}, inplace=True)   
                
                            amplitude_each = max_df_value - baseline_each
                            signal_rise = (int(peak__frame_static)-int(baseline__frame_static))/frame_rate
                            signal_decay = (int(recovery_baseline__frame_static)-int(peak__frame_static))/frame_rate
                            signal_duration = (int(recovery_baseline__frame_static)-int(baseline__frame_static))/frame_rate
                            nested_dict_pro["Label"].append(i)
                            nested_dict_pro["Number of Events"].append(1)
                            nested_dict_pro["Rise time"].append(signal_rise)
                            nested_dict_pro["Decay time"].append(signal_decay)
                            nested_dict_pro["Duration"].append(signal_duration)
                            nested_dict_pro["Amplitude"].append(amplitude_each)
                            a_est_rise = rise_df['Rise intensity'].iloc[-1]
                            b_est_rise = find_b_est_rise(np.array(rise_df['Frame']), np.array(rise_df['Rise intensity']))
                            a_est = decay_df['Decay intensity'].iloc[0]
                            b_est = find_b_est_decay(np.array(decay_df['Frame']), np.array(decay_df['Decay intensity'])) 
                            
                            try:
                                popt_decay, pcov_decay = curve_fit(mono_exp_decay, decay_df['Frame'], decay_df['Decay intensity'], p0=[a_est,b_est])
                                
                            except (TypeError, RuntimeError) as e:
                                error_message = str(e)
                                if error_message == "Optimal parameters not found: Number of calls to function has reached maxfev = 600":
                                    # Handle the error and continue to the next iteration
                                    pass
                                #st.write("here")
                                # Replace the error with a warning message
                                else:
                                    warning_message = "Fitting cannot be performed"
                                    warnings.warn(warning_message, category=UserWarning)
                                    popt_decay, pcov_decay = None, None
                                    nested_dict_pro["Decay Rate"].append(popt_decay)
                            else: 
                                popt_decay, pcov_decay = curve_fit(mono_exp_decay, decay_df['Frame'], decay_df['Decay intensity'], p0=[a_est,b_est])
                                decay_curve_exp = mono_exp_decay(decay_df['Frame'], *popt_decay)
                                nested_dict_pro["Decay Rate"].append(np.round(popt_decay[1],4))
                                
                            try:
                                popt_rise, pcov_rise = curve_fit(mono_exp_rise, rise_df['Frame'], rise_df['Rise intensity'], p0=[a_est_rise,b_est_rise])
                                
                            except (TypeError, RuntimeError) as e:
                                error_message = str(e)
                                if error_message == "Optimal parameters not found: Number of calls to function has reached maxfev = 600":
                                    pass
                                # Replace the error with a warning message
                                else:                           
                                    warning_message = "Fitting cannot be performed"
                                    warnings.warn(warning_message, category=UserWarning)
                                    popt_rise, pcov_rise = None, None
                                    nested_dict_pro["Decay Rate"].append(popt_decay)
                                    #bounds = ([0, 0], [100, 100])
                                    #st.write(a_est)
                            else:
                                popt_rise, pcov_rise = curve_fit(mono_exp_rise, rise_df['Frame'], rise_df['Rise intensity'], p0=[a_est_rise,b_est_rise])
                                rise_curve_exp = np.round((mono_exp_rise(rise_df['Frame'], *popt_rise)),3) 
                                nested_dict_pro["Rise Rate"].append(np.round(popt_rise[1], 4))
                            nested_dict_final = nested_dict_pro.copy()  
                            nested_dict_final = (pd.DataFrame.from_dict(nested_dict_final))
                            #st.write(nested_dict_final)
                    elif baseline_recovery_frame_input ==   'Average Frame Value': 
                        for i in df_selected['label']:
                            baseline_each = new_df_pro_transposed_smooth.loc[(new_df_pro_transposed_smooth['Frame'] >= 0) & (new_df_pro_transposed_smooth['Frame'] <= baseline_smooth_x), f'smooth cell {i}'].mean()
                            baseline_mean_each = new_df_pro_transposed_smooth.loc[(new_df_pro_transposed_smooth['Frame'] >= 0) & (new_df_pro_transposed_smooth['Frame'] <= baseline_smooth_x), float(f'{i}.0')].mean()                    
                            baseline__frame_static = int(sum(range(baseline_smooth_x + 1)) / (baseline_smooth_x + 1))                       
                            new_df_pro_transposed_smooth[f'smooth cell {i}'] = new_df_pro_transposed_smooth[f'smooth cell {i}']/baseline_each
                            baseline_each = baseline_each/baseline_each                    
                            new_df_pro_transposed_smooth[f'delta_f/f_0_{i}'] = (new_df_pro_transposed_smooth[f'smooth cell {i}'] - baseline_each)/baseline_each         
                            filtered_peak_each = new_df_pro_transposed_smooth.query("Frame == @peak__frame_static")
                            max_df_value = filtered_peak_each[f'smooth cell {i}'].iloc[0]
                            rise_df = new_df_pro_transposed_smooth[(new_df_pro_transposed_smooth['Frame'] >= baseline__frame_static) & (new_df_pro_transposed_smooth['Frame'] <= peak__frame_static)]
                            decay_df = new_df_pro_transposed_smooth[(new_df_pro_transposed_smooth['Frame'] >= peak__frame_static) & (new_df_pro_transposed_smooth['Frame'] <= recovery_baseline__frame_static)]
                            decay_df = decay_df[['Frame', f'smooth cell {i}']]
                            decay_df.rename(columns={f'smooth cell {i}': 'Decay intensity'}, inplace=True)
                            rise_df = rise_df[['Frame', f'smooth cell {i}']]
                            rise_df.rename(columns={f'smooth cell {i}': 'Rise intensity'}, inplace=True)   
                
                            amplitude_each = max_df_value - baseline_each
                            signal_rise = (int(peak__frame_static)-int(baseline__frame_static))/frame_rate
                            signal_decay = (int(recovery_baseline__frame_static)-int(peak__frame_static))/frame_rate
                            signal_duration = (int(recovery_baseline__frame_static)-int(baseline__frame_static))/frame_rate
                            nested_dict_pro["Label"].append(i)
                            nested_dict_pro["Number of Events"].append(1)
                            nested_dict_pro["Rise time"].append(signal_rise)
                            nested_dict_pro["Decay time"].append(signal_decay)
                            nested_dict_pro["Duration"].append(signal_duration)
                            nested_dict_pro["Amplitude"].append(amplitude_each)
                            a_est_rise = rise_df['Rise intensity'].iloc[-1]
                            b_est_rise = find_b_est_rise(np.array(rise_df['Frame']), np.array(rise_df['Rise intensity']))
                            a_est = decay_df['Decay intensity'].iloc[0]
                            b_est = find_b_est_decay(np.array(decay_df['Frame']), np.array(decay_df['Decay intensity'])) 
                            
                            try:
                                popt_decay, pcov_decay = curve_fit(mono_exp_decay, decay_df['Frame'], decay_df['Decay intensity'], p0=[a_est,b_est])
                                
                            except (TypeError, RuntimeError) as e:
                                error_message = str(e)
                                if error_message == "Optimal parameters not found: Number of calls to function has reached maxfev = 600":
                                    # Handle the error and continue to the next iteration
                                    pass
                                #st.write("here")
                                # Replace the error with a warning message
                                else:
                                    warning_message = "Fitting cannot be performed"
                                    warnings.warn(warning_message, category=UserWarning)
                                    popt_decay, pcov_decay = None, None
                                    nested_dict_pro["Decay Rate"].append(popt_decay)
                            else: 
                                popt_decay, pcov_decay = curve_fit(mono_exp_decay, decay_df['Frame'], decay_df['Decay intensity'], p0=[a_est,b_est])
                                decay_curve_exp = mono_exp_decay(decay_df['Frame'], *popt_decay)
                                nested_dict_pro["Decay Rate"].append(np.round(popt_decay[1], 4))
                            try:
                                popt_rise, pcov_rise = curve_fit(mono_exp_rise, rise_df['Frame'], rise_df['Rise intensity'], p0=[a_est_rise,b_est_rise])
                                
                            except (TypeError, RuntimeError) as e:
                                error_message = str(e)
                                if error_message == "Optimal parameters not found: Number of calls to function has reached maxfev = 600":
                                    pass
                                # Replace the error with a warning message
                                else:                           
                                    warning_message = "Fitting cannot be performed"
                                    warnings.warn(warning_message, category=UserWarning)
                                    popt_rise, pcov_rise = None, None
                                    nested_dict_pro["Rise Rate"].append(popt_rise)
                                    #bounds = ([0, 0], [100, 100])
                                    #st.write(a_est)
                            else:
                                popt_rise, pcov_rise = curve_fit(mono_exp_rise, rise_df['Frame'], rise_df['Rise intensity'], p0=[a_est_rise,b_est_rise])
                                rise_curve_exp = np.round((mono_exp_rise(rise_df['Frame'], *popt_rise)),3) 
                                nested_dict_pro["Rise Rate"].append(np.round(popt_rise[1], 4))
                            nested_dict_final = nested_dict_pro.copy()  
                            nested_dict_final = (pd.DataFrame.from_dict(nested_dict_final))
                            
                    st.write(new_df_pro_transposed_smooth)
                    multi_csv = convert_df(new_df_pro_transposed_smooth)           
                    st.download_button("Press to Download",  multi_csv, 'multi_cell_data.csv', "text/csv", key='download_multi_-csv_stat')                
                    #st.write(nested_dict_final)
                    #nested_dict_final = nested_dict_pro.copy()
                    #nested_dict_final = (pd.DataFrame.from_dict(nested_dict_final)) 
                    traces_smooth = []                    
                    column_new_df = new_df_pro_transposed_smooth.columns              
                    for smooth_column in column_new_df:    
                        if "smooth cell" in str(smooth_column):
                            # create a trace for the current column
                            trace_smooth = go.Scatter(x=new_df_pro_transposed_smooth['Time'], y=new_df_pro_transposed_smooth[smooth_column], name=smooth_column)
                            # add the trace to the list
                            traces_smooth.append(trace_smooth)
                    # create the plot
                    fig_smooth = go.Figure(data=traces_smooth)
                    # update the layout
                    fig_smooth.update_layout(title='Normalized Intensity Traces', xaxis_title='Time', yaxis_title='Normalized Intensity',height=900)
                    # display the plot
                    st.plotly_chart(fig_smooth, use_container_width=True)                       
                    if nested_dict_final.empty:
                        pass
                    else:                              
                        st.subheader("**_Parameters for selected labels_**")
                        col_7, col_8 = st.columns(2)
                        
                        with col_7: 
                            nested_dict_final = nested_dict_final[nested_dict_final.groupby('Label')['Amplitude'].transform(max) == nested_dict_final['Amplitude']]
                            nested_dict_final['Number of Events'] = nested_dict_final.groupby('Label')['Number of Events'].transform('count')
    
                            st.write(nested_dict_final)  
                            all_csv = convert_df(nested_dict_final)           
                            st.download_button("Press to Download", all_csv, 'all_data.csv', "text/csv", key='all_download-csv')
                        with col_8:
                            average_rise_time = np.round(nested_dict_final['Rise time'].mean(),4)
                            st.write(f"The average rise time based on selected labels across all frames is {average_rise_time} s")
                            average_rise_rate = np.round(nested_dict_final['Rise Rate'].mean(),4)
                            st.write(f"The average rise rate based on selected labels across all frames is {average_rise_rate} per s")
                            average_decay_time = np.round(nested_dict_final['Decay time'].mean(),4)
                            st.write(f"The average decay time based on selected labels across all frames is {average_decay_time} s")
                            average_decay_rate = np.round(nested_dict_final['Decay Rate'].mean(),4)
                            st.write(f"The average decay rate based on selected labels across all frames is {average_decay_rate} per s")
                            average_duration = np.round(nested_dict_final['Duration'].mean(),4)
                            st.write(f"The average duration based on selected labels across all frames is {average_duration} s")
                            average_amplitude = np.round(nested_dict_final['Amplitude'].mean(),4)
                            st.write(f"The average amplitude based on selected labels across all frames is {average_amplitude}")                
                        nested_dict_final['Amplitude'] = np.round(nested_dict_final['Amplitude'], 2)    
                        nested_dict_final['Duration'] = np.round(nested_dict_final['Duration'], 2)   
                        nested_dict_final['Decay time'] = np.round(nested_dict_final['Decay time'], 2)  
                        nested_dict_final['Rise time'] = np.round(nested_dict_final['Rise time'], 2) 
                        nested_dict_final['Rise Rate'] = np.round(nested_dict_final['Rise Rate'], 2)
                        nested_dict_final['Decay Rate'] = np.round(nested_dict_final['Decay Rate'], 2)
                        
                        exclude_columns = ['Label', 'Number of Events']
                        columns_to_plot = [col for col in nested_dict_final.columns if col not in exclude_columns]
                        
                        fig = make_subplots(rows=3, cols=2, subplot_titles = ["A", "B", "C", "D", "E", "F"])                      
                        for i, colu in enumerate(columns_to_plot):
                            row = i // 2 + 1
                            col = i % 2 + 1                            
                            fig.add_trace(go.Histogram(x=nested_dict_final[colu], name=colu, nbinsx=20, marker_line_color='black', marker_line_width=1), row=row, col=col)                                   
                        fig.update_layout(title="Histograms",height=1000, width=800, showlegend=False)
                        fig.update_xaxes(title_text="Rise time (s)", row=1, col=1)
                        fig.update_xaxes(title_text="Rise Rate (s⁻¹)", row=1, col=2)
                        fig.update_xaxes(title_text="Decay time (s)", row=2, col=1)
                        fig.update_xaxes(title_text="Decay Rate (s⁻¹)", row=2, col=2)
                        fig.update_xaxes(title_text="Duration (s)", row=3, col=1)
                        fig.update_xaxes(title_text="Amplitude", row=3, col=2)
                        fig.update_yaxes(title_text="Number of selected cells", row=1, col=1)
                        fig.update_yaxes(title_text="Number of selected cells", row=2, col=1)
                        fig.update_yaxes(title_text="Number of selected cells", row=3, col=1)
                        st.plotly_chart(fig)  
                               
                        st.warning('Navigating to another page from the sidebar will remove all selections from the current page')
        if bleach_corr_check == 'Bleaching correction':
            baseline_peak_selection = st.radio("Select one", ('Static', 'Dynamic'), help='Select "Static" to manually select single values for the baseline, peak and recovery frames; otherwise, select "Dynamic"')
            smooth_plot_x = st.number_input("*_Moving Average Window_*", min_value=1, max_value=5, help = "Adjust to smooth the mean intensity trace below. Moving average of 1 would mean the original 'Mean Intensity' trace")
            fit_first_x = st.number_input("*_Choose the number of first few frame number(s) to fit a mono-exponential decay_*", min_value = 1, max_value = int(np.floor(raw_img_ani_pg_2.shape[0]/2)), value = 30,  key='smooth_fit_first_multi')
            fit_last_x = st.number_input("*_Choose the number of last few frame number(s) to fit a mono-exponential decay_*", 1, int(np.floor(raw_img_ani_pg_2.shape[0]/2)), value = 30, key='smooth_fit_last_multi')
            fit_last_x = raw_img_ani_pg_2.shape[0] - 1 - fit_last_x
            if baseline_peak_selection == "Dynamic": 
                baseline_smooth_x = st.number_input("*_Choose frame number(s) to average their corresponding intensity values for baseline calculation_*", min_value = 0, max_value = raw_img_ani_pg_2.shape[0]-1, value = 10,  key='smooth_multi_0') 
                if st.button("Obtain the parameters for selected labels",on_click=callback_movav) or st.session_state.button_clicked_movav:
                    
                    st.warning("The parameters for all labels are obtained using the same set of selections.")
                    df_pro_pixel_remove = df_selected_1.drop(columns=df_selected.filter(regex='^Bright_pixel_area_').columns)
                    #df_pro_pixel_remove = df_pro_pixel_remove.drop(columns=df_pro.filter(regex='^area').columns)
                    new_df_pro_transposed_smooth = df_pro_pixel_remove.transpose()
                    new_df_pro_transposed_smooth.columns = new_df_pro_transposed_smooth.iloc[0]
                    new_df_pro_transposed_smooth.drop(new_df_pro_transposed_smooth.index[0], inplace=True)                     
                    
                    #smooth_plot_x = st.slider("*_Moving Average Window_*", min_value=1, max_value=5, help = "Select to smooth the intensity trace. Moving average of 1 would mean the original 'Mean Intensity' trace below", key = 'mov_av')
                    for i in df_selected['label']: 
                        
                        df_pro_transposed_smooth = pd.DataFrame(smooth_plot(new_df_pro_transposed_smooth[i],smooth_plot_x),columns = [f'smooth cell {i}'])
                        new_df_pro_transposed_smooth = pd.concat([new_df_pro_transposed_smooth.reset_index(drop=True), (np.round(df_pro_transposed_smooth[f'smooth cell {i}'],3)).reset_index(drop=True)],axis=1)
                        new_df_missing_values = pd.isna(new_df_pro_transposed_smooth[f"smooth cell {i}"])
                        new_df_pro_transposed_smooth.loc[new_df_missing_values, f'smooth cell {i}'] = new_df_pro_transposed_smooth.loc[new_df_missing_values, i] 
                        new_df_pro_transposed_smooth['Frame'] = pd.DataFrame(list(range(0, df_selected.shape[1])))      
                        baseline_each = new_df_pro_transposed_smooth.loc[(new_df_pro_transposed_smooth['Frame'] >= 0) & (new_df_pro_transposed_smooth['Frame'] <= baseline_smooth_x), f'smooth cell {i}'].mean()
                        new_df_pro_transposed_smooth[f"smooth cell {i}"] = new_df_pro_transposed_smooth[f"smooth cell {i}"]/baseline_each
                        #st.write(new_df_pro_transposed)
                    
                    new_df_pro_transposed_smooth = new_df_pro_transposed_smooth.iloc[:, [new_df_pro_transposed_smooth.shape[1] - 1] + list(range(new_df_pro_transposed_smooth.shape[1] - 1))]
                    new_df_pro_transposed_smooth['Time'] = new_df_pro_transposed_smooth['Frame']/frame_rate                   

                    nested_dict_final = {}           
                    nested_dict_pro = {'Label':[], "Number of Events":[], "Rise time":[], "Rise Rate":[], "Decay time":[], "Decay Rate":[], "Duration":[], "Amplitude":[]}  
                    
                    plot_df_corr = pd.DataFrame()
                    plot_df_corr['Frame'] = new_df_pro_transposed_smooth['Frame']
                    plot_df_corr['Time'] = plot_df_corr['Frame']/frame_rate
                    for i in df_selected['label']: 
                        
                        column_corr_first = new_df_pro_transposed_smooth.loc[(new_df_pro_transposed_smooth['Frame'] >= 0) & (new_df_pro_transposed_smooth['Frame'] <= fit_first_x), f'smooth cell {i}']
                        exp_df_1 = pd.DataFrame({f'Bleach intensity {i}': column_corr_first})
                        exp_df_1['Frames'] = new_df_pro_transposed_smooth[0:fit_first_x+1]['Frame']
                        column_corr_last = new_df_pro_transposed_smooth.loc[(new_df_pro_transposed_smooth['Frame'] >= fit_last_x) & (new_df_pro_transposed_smooth['Frame'] <= raw_img_ani_pg_2.shape[0]-1), f'smooth cell {i}']
                        exp_df_2 = pd.DataFrame({f'Bleach intensity {i}': column_corr_last})
                        exp_df_2['Frames'] = new_df_pro_transposed_smooth[fit_last_x:raw_img_ani_pg_2.shape[0]]['Frame']                   
                        exp_df = pd.concat([exp_df_1, exp_df_2], axis=0)
                        #st.write(exp_df)
                        popt_exp, pcov_exp = curve_fit(mono_exp_decay, exp_df['Frames'], exp_df[f'Bleach intensity {i}'], p0 = [np.max(exp_df['Frames']), find_b_est_decay(np.array(exp_df['Frames']), np.array(exp_df[f'Bleach intensity {i}']))])
                        photobleach_curve_exp = mono_exp_decay(new_df_pro_transposed_smooth['Frame'], *popt_exp)           
                        fit_exp_df = pd.DataFrame()
                        fit_exp_df['Frame'] = new_df_pro_transposed_smooth['Frame']
                        fit_exp_df['Photobleach Corr'] = photobleach_curve_exp
                        
                        plot_df_corr_intensity = new_df_pro_transposed_smooth[f'smooth cell {i}']-photobleach_curve_exp
                        plot_df_corr_intensity_min = min(plot_df_corr_intensity)                    
                        plot_df_corr_value = pd.DataFrame(np.round((plot_df_corr_intensity + abs(plot_df_corr_intensity_min)),3), columns = [f'smooth cell {i}'])
                        plot_df_corr = pd.concat([plot_df_corr.reset_index(drop=True), plot_df_corr_value] ,axis=1)
                        plot_df_corr.loc[plot_df_corr[f'smooth cell {i}'] == 0, f'smooth cell {i}'] = plot_df_corr[f'smooth cell {i}'].replace(0, plot_df_corr[f'smooth cell {i}'][plot_df_corr[f'smooth cell {i}'] != 0].min())
                        #plot_df_corr['Smoothed Mean Intensity'][plot_df_corr['Smoothed Mean Intensity']<0] = 0
                        baseline_corr_each = plot_df_corr.loc[(plot_df_corr['Frame'] >= 0) & (plot_df_corr['Frame'] <= baseline_smooth_x), f'smooth cell {i}'].mean()
                        delta = np.round((plot_df_corr[f'smooth cell {i}']-baseline_corr_each)/baseline_corr_each,3)
                        plot_df_corr_value_delta = pd.DataFrame(list(delta), columns = [f'delta_f/f_0_{i}'])
                        plot_df_corr = pd.concat([plot_df_corr.reset_index(drop=True), plot_df_corr_value_delta],axis=1)

                        keyval = {}
                        amp_keyval = {}
                        prev_intensity = 0
                        flag = 1
                        for frame_key, intensity_val in enumerate(plot_df_corr[f'smooth cell {i}']):
                            if prev_intensity == 0 and intensity_val > baseline_corr_each:
                                continue
                            elif intensity_val >= baseline_corr_each:
                                keyval[frame_key] = intensity_val
                                break
                            else:
                                if frame_key==len(plot_df_corr.index)-1:
                                    flag = 0
                                else:
                                    prev_intensity = intensity_val
                                    continue
                        if flag==0:
                            prev_intensity = 0
                            continue
                        
                        first_key = frame_key
                        first_intensity = keyval[frame_key]
                        
                        prev_intensity = keyval[frame_key]
                        for frame_key_2, intensity_val_2 in enumerate(plot_df_corr[f'smooth cell {i}']):                               
                            if frame_key_2 <= frame_key:
                                continue
                            elif frame_key_2 > frame_key:
                                if intensity_val_2 >= prev_intensity:
                                    if intensity_val_2 < baseline_corr_each:
                                        frame_key = frame_key_2
                                        continue
                                    elif intensity_val_2 >= baseline_corr_each:
                                        if prev_intensity < baseline_corr_each:
                                            first_key = frame_key_2
                                            first_intensity = intensity_val_2
                                            keyval[first_key] = first_intensity
                                            frame_key = frame_key_2
                                            prev_intensity = intensity_val_2
                                        else:
                                            frame_key = frame_key_2
                                            prev_intensity = intensity_val_2
                                        
                
                                elif intensity_val_2 < prev_intensity:
                                    if intensity_val_2 > baseline_corr_each:
                                        frame_key = frame_key_2                                         
                                    elif intensity_val_2 <= baseline_corr_each:
                                        if prev_intensity <= baseline_corr_each:
                                            frame_key = frame_key_2
                                            continue
                                        else:
                                            keyval[frame_key_2] = intensity_val_2
                                            frame_key = frame_key_2
                                            #start_key = plot_df.query(f'"Smoothed Mean Intensity" == {prev_intensity}')['Frame']
                                            amp_key_vals = plot_df_corr[plot_df_corr[f'smooth cell {i}']==prev_intensity]['Frame']
                                            amp_key_vals = amp_key_vals[amp_key_vals>=first_key].iloc[0]
                                            amp_key = str(amp_key_vals)
                                            #amp_key = str(new_df_pro_transposed_smooth[new_df_pro_transposed_smooth[f'smooth cell {i}']==prev_intensity]['Frame'].iloc[0])
                                            amplitude = prev_intensity - baseline_corr_each
                                            keyval[amp_key] = prev_intensity
                                            prev_intensity = intensity_val_2
                                            if (first_key == int(amp_key)): #or (int(amp_key) == frame_key): 
                                                first_key = int(amp_key)-1
                                                amp_keyval[f"{first_key}-{amp_key}-{frame_key}"] = amplitude
                                            else:
                                                amp_keyval[f"{first_key}-{amp_key}-{frame_key}"] = amplitude                
                        
                        
                        max_df_value = plot_df_corr[f'smooth cell {i}'].max()
                        #####test by setting a some equal high values#########plot_df.loc[plot_df['Frame'] == 39, 'Smoothed Mean Intensity'] = max_df_value ##plot_df.loc[plot_df['Frame'] == 69, 'Smoothed Mean Intensity'] = baseline_each
                        count_max = plot_df_corr[f'smooth cell {i}'].eq(max_df_value).sum()
                        max_frame = plot_df_corr.loc[plot_df_corr[f'smooth cell {i}'] == max_df_value, 'Frame']
                        decay_df = pd.DataFrame()
                        rise_df = pd.DataFrame()
    
                        if ((plot_df_corr.loc[plot_df_corr["Frame"].gt(max(max_frame)), f'smooth cell {i}']).gt(baseline_corr_each)).all(): ##trace crosses baseline but never comes back
                            #nested_dict_pro = {'Label':[], "Number of Events":[], "Rise time":[], "Rise Rate":[], "Decay time":[], "Decay Rate":[], "Duration":[], "Amplitude":[]}
                           if count_max == 1:
                            rise_df['Rise intensity'] = plot_df_corr.loc[(plot_df_corr[f'smooth cell {i}'] <= max_df_value) & (plot_df_corr[f'smooth cell {i}'] >= baseline_corr_each) & (plot_df_corr['Frame'] <= max(max_frame)) , f'smooth cell {i}']
                            rise_df['Frame'] = rise_df.index
                            rise_df = rise_df[rise_df.columns[::-1]]
                            missing_value_rise_df = (rise_df.loc[rise_df['Frame'].diff() > 1, 'Frame'].max())-1
                            #st.write(~rise_df['Rise intensity'].isin([baseline_each]).any())
                            # if ~decay_df['Decay intensity'].isin([baseline_each]).any():
                            #     new_row_decay = {'Frame':  missing_value_df, 'Decay intensity': baseline_each}
                            #     decay_df.loc[len(decay_df)] = new_row_decay
                            # if ~rise_df['Rise intensity'].isin([baseline_each]).any():
                            #     new_row_rise = {'Frame':  missing_value_rise_df, 'Rise intensity': baseline_each}
                            #     rise_df.loc[missing_value_rise_df] = new_row_rise
                            
                            #decay_df.loc[decay_df['Frame'] == missing_value_df, 'Decay intensity'] == baseline_each
                            #st.write(missing_value_df)
                                
                            if not pd.isna(missing_value_rise_df):
                                #st.write('here')
                                rise_df = rise_df.loc[rise_df['Frame'] >= missing_value_rise_df]
                            else:
                                if (rise_df['Rise intensity'] == baseline_corr_each).any():
                                    #st.write(rise_df)
                                    baseline_frame = max(rise_df.loc[rise_df['Rise intensity'] == baseline_corr_each, 'Frame'])
                                    rise_df = rise_df.loc[(rise_df['Rise intensity'] >= baseline_corr_each) & (rise_df['Frame'] >= baseline_frame)]  
                                else:
                                    rise_df = rise_df   
                            
                            #st.write(missing_value_df)
                            
                            if count_max > 1: 
                                                        
                                rise_df['Rise intensity'] = plot_df_corr.loc[(plot_df_corr[f'smooth cell {i}'] <= max_df_value) & (plot_df_corr[f'smooth cell {i}'] >= baseline_corr_each) & (plot_df_corr['Frame'] <= min(max_frame)) , f'smooth cell {i}']
                                first_index = rise_df.loc[rise_df['Rise intensity'] == max_df_value].index[-1]                    
                                #rise_df.loc[first_index, 'Rise intensity'] *= 1.01                        
                                rise_df['Frame'] = rise_df.index
                                rise_df = rise_df[rise_df.columns[::-1]]
                                #st.write(decay_df)
                                
                                missing_value_rise_df = (rise_df.loc[rise_df['Frame'].diff() > 1, 'Frame'].max())-1
                                #st.write(np.any(rise_df['Rise intensity']) != baseline_each)
                                # if ~decay_df['Decay intensity'].isin([baseline_each]).any():
                                #     if missing_value_df is not None:
                                #         new_row_decay = {'Frame':  missing_value_df, 'Decay intensity': baseline_each}
                                #         decay_df.loc[len(decay_df)] = new_row_decay
                                # if ~rise_df['Rise intensity'].isin([baseline_each]).any():
                                #     if missing_value_rise_df is not None:
                                #         new_row_rise = {'Frame':  missing_value_rise_df, 'Rise intensity': baseline_each}
                                #         rise_df.loc[missing_value_rise_df] = new_row_rise
                                #decay_df.loc[decay_df['Frame'] == missing_value_df, 'Decay intensity'] == baseline_each
                                #st.write(missing_value_rise_df)
                                    
                                if not pd.isna(missing_value_rise_df):
                                    #st.write('here')
                                    rise_df = rise_df.loc[rise_df['Frame'] >= missing_value_rise_df]
                                else:
                                    if (rise_df['Rise intensity'] == baseline_corr_each).any():
                                        #st.write(rise_df)
                                        baseline_frame = max(rise_df.loc[rise_df['Rise intensity'] == baseline_corr_each, 'Frame'])
                                        rise_df = rise_df.loc[(rise_df['Rise intensity'] >= baseline_corr_each) & (rise_df['Frame'] >= baseline_frame)]  
                                    else:
                                        rise_df = rise_df          
                                           
                            a_est_rise = rise_df['Rise intensity'].iloc[-1]
                            b_est_rise = find_b_est_rise(np.array(rise_df['Frame']), np.array(rise_df['Rise intensity']))
                            #bounds = ([0, 0], [100, 100])
                            
                            popt_decay, pcov_decay = None, None                        
                            
                            try:
                                popt_rise, pcov_rise = curve_fit(mono_exp_rise, rise_df['Frame'], rise_df['Rise intensity'], p0=[a_est_rise,b_est_rise])
                                
                            except (TypeError, RuntimeError) as e:
                                error_message = str(e)
                                if error_message == "Optimal parameters not found: Number of calls to function has reached maxfev = 600":
                                    pass
                                # Replace the error with a warning message
                                else:                           
                                    warning_message = "Fitting cannot be performed"
                                    warnings.warn(warning_message, category=UserWarning)
                                    popt_rise, pcov_rise = None, None
                                    #bounds = ([0, 0], [100, 100])
                                    #st.write(a_est)
                            else:
                                popt_rise, pcov_rise = curve_fit(mono_exp_rise, rise_df['Frame'], rise_df['Rise intensity'], p0=[a_est_rise,b_est_rise])
                                rise_curve_exp = np.round((mono_exp_rise(rise_df['Frame'], *popt_rise)),3)  
                                
                            signal_rise = (max(max_frame) - rise_df['Frame'].iloc[0])/frame_rate
                            amplitude_each = max_df_value - baseline_corr_each
                            if (pcov_decay is None) and (popt_decay is None):
                                nested_dict_pro["Label"].append(i)
                                nested_dict_pro["Number of Events"].append(None)
                                nested_dict_pro["Rise time"].append(signal_rise)
                                nested_dict_pro["Decay time"].append(None)
                                nested_dict_pro["Duration"].append(None)
                                nested_dict_pro["Amplitude"].append(amplitude_each) 
                                if popt_rise is not None:
                                    rise_rate = np.round(popt_rise[1],4)
                                    nested_dict_pro["Rise Rate"].append(rise_rate)
                                else:
                                    nested_dict_pro["Rise Rate"].append(None)
                                nested_dict_pro["Decay Rate"].append(None)
                            
                        else:
                            
                            if count_max == 1:
                                rise_df['Rise intensity'] = plot_df_corr.loc[(plot_df_corr[f'smooth cell {i}'] <= max_df_value) & (plot_df_corr[f'smooth cell {i}'] >= baseline_corr_each) & (plot_df_corr['Frame'] <= max(max_frame)) , f'smooth cell {i}']
                                decay_df['Decay intensity'] = plot_df_corr.loc[(plot_df_corr[f'smooth cell {i}'] <= max_df_value) & (plot_df_corr[f'smooth cell {i}'] >= baseline_corr_each) & (plot_df_corr['Frame'] >= max(max_frame)) , f'smooth cell {i}']
                                decay_df['Frame'] = decay_df.index
                                rise_df['Frame'] = rise_df.index
                                decay_df = decay_df[decay_df.columns[::-1]]
                                rise_df = rise_df[rise_df.columns[::-1]]
                                test_missing_value_df = next((decay_df['Frame'].iloc[i] + 1 for i in range(len(decay_df['Frame'])-1) if decay_df['Frame'].iloc[i+1] - decay_df['Frame'].iloc[i] > 1), None)
                                if test_missing_value_df is None:
                                    missing_value_df = None
                                else:
                                    missing_value_df = test_missing_value_df - 1 
                                missing_value_rise_df = (rise_df.loc[rise_df['Frame'].diff() > 1, 'Frame'].max())-1
                                #st.write(~rise_df['Rise intensity'].isin([baseline_each]).any())
                                # if ~decay_df['Decay intensity'].isin([baseline_each]).any():
                                #     new_row_decay = {'Frame':  missing_value_df, 'Decay intensity': baseline_each}
                                #     decay_df.loc[len(decay_df)] = new_row_decay
                                # if ~rise_df['Rise intensity'].isin([baseline_each]).any():
                                #     new_row_rise = {'Frame':  missing_value_rise_df, 'Rise intensity': baseline_each}
                                #     rise_df.loc[missing_value_rise_df] = new_row_rise
                                
                                #decay_df.loc[decay_df['Frame'] == missing_value_df, 'Decay intensity'] == baseline_each
                                #st.write(missing_value_df)
                                if not pd.isna(missing_value_df): #there is a missing value
                                    #st.write('here')
                                    decay_df = decay_df.loc[decay_df['Frame'] <= missing_value_df]
                                 
                                else:
                                    if (decay_df['Decay intensity'] == baseline_corr_each).any():
                                        baseline_frame = max(decay_df.loc[decay_df['Decay intensity'] == baseline_corr_each, 'Frame'])
                                        decay_df = decay_df.loc[(decay_df['Decay intensity'] >= baseline_corr_each) & (decay_df['Frame'] <= baseline_frame)]  
                                    else:
                                        decay_df = decay_df
                                    
                                if not pd.isna(missing_value_rise_df):
                                    #st.write('here')
                                    rise_df = rise_df.loc[rise_df['Frame'] >= missing_value_rise_df]
                                else:
                                    if (rise_df['Rise intensity'] == baseline_corr_each).any():
                                        #st.write(rise_df)
                                        baseline_frame = max(rise_df.loc[rise_df['Rise intensity'] == baseline_corr_each, 'Frame'])
                                        rise_df = rise_df.loc[(rise_df['Rise intensity'] >= baseline_corr_each) & (rise_df['Frame'] >= baseline_frame)]  
                                    else:
                                        rise_df = rise_df
                                #st.write(rise_df)
                                #st.write(missing_value_df)
                                
                            if count_max > 1: 
    
                                decay_df['Decay intensity'] = plot_df_corr.loc[(plot_df_corr[f'smooth cell {i}'] <= max_df_value) & (plot_df_corr[f'smooth cell {i}'] >= baseline_corr_each) & (plot_df_corr['Frame'] >= max(max_frame)) , f'smooth cell {i}']
                                last_index = decay_df.loc[decay_df['Decay intensity'] == max_df_value].index[-1]
                                rise_df['Rise intensity'] = plot_df_corr.loc[(plot_df_corr[f'smooth cell {i}'] <= max_df_value) & (plot_df_corr[f'smooth cell {i}'] >= baseline_corr_each) & (plot_df_corr['Frame'] <= min(max_frame)) , f'smooth cell {i}']
                                first_index = rise_df.loc[rise_df['Rise intensity'] == max_df_value].index[0]                    
                                #decay_df.loc[last_index, 'Decay intensity'] *= 1.01
                                #rise_df.loc[first_index, 'Rise intensity'] *= 1.01
                                decay_df['Frame'] = decay_df.index
                                rise_df['Frame'] = rise_df.index
                                decay_df = decay_df[decay_df.columns[::-1]]
                                rise_df = rise_df[rise_df.columns[::-1]]
                                #st.write(rise_df)
                                #st.write(decay_df)
                                test_missing_value_df = next((decay_df['Frame'].iloc[i] + 1 for i in range(len(decay_df['Frame'])-1) if decay_df['Frame'].iloc[i+1] - decay_df['Frame'].iloc[i] > 1), None)
                                if test_missing_value_df is None:
                                    missing_value_df = None
                                else:
                                    missing_value_df = test_missing_value_df - 1                         
                                missing_value_rise_df = (rise_df.loc[rise_df['Frame'].diff() > 1, 'Frame'].max())-1
                                #st.write(np.any(rise_df['Rise intensity']) != baseline_each)
                                # if ~decay_df['Decay intensity'].isin([baseline_corr_each]).any():
                                #     new_row_decay = {'Frame':  missing_value_df, 'Decay intensity': baseline_corr_each}
                                #     decay_df.loc[len(decay_df)] = new_row_decay
                                # if ~rise_df['Rise intensity'].isin([baseline_corr_each]).any():
                                #     new_row_rise = {'Frame':  missing_value_rise_df, 'Rise intensity': baseline_corr_each}
                                #     rise_df.loc[missing_value_rise_df] = new_row_rise
                                #decay_df.loc[decay_df['Frame'] == missing_value_df, 'Decay intensity'] == baseline_each
                                #st.write(missing_value_rise_df)
                                if not pd.isna(missing_value_df):
                                    #st.write('here')
                                    decay_df = decay_df.loc[decay_df['Frame'] <= missing_value_df]
                                else:
                                    if (decay_df['Decay intensity'] == baseline_corr_each).any():
                                        baseline_frame = max(decay_df.loc[decay_df['Decay intensity'] == baseline_corr_each, 'Frame'])
                                        decay_df = decay_df.loc[(decay_df['Decay intensity'] >= baseline_corr_each) & (decay_df['Frame'] <= baseline_frame)]  
                                    else:
                                        decay_df = decay_df
                                    
                                if not pd.isna(missing_value_rise_df):
                                    #st.write('here')
                                    rise_df = rise_df.loc[rise_df['Frame'] >= missing_value_rise_df]
                                else:
                                    if (rise_df['Rise intensity'] == baseline_corr_each).any():
                                        #st.write(rise_df)
                                        baseline_frame = max(rise_df.loc[rise_df['Rise intensity'] == baseline_corr_each, 'Frame'])
                                        rise_df = rise_df.loc[(rise_df['Rise intensity'] >= baseline_corr_each) & (rise_df['Frame'] >= baseline_frame)]  
                                    else:
                                        rise_df = rise_df             
                                #st.write(rise_df)
                            
                            a_est = decay_df['Decay intensity'].iloc[0]
                            b_est = find_b_est_decay(np.array(decay_df['Frame']), np.array(decay_df['Decay intensity']))
                            a_est_rise = rise_df['Rise intensity'].iloc[-1]
                            b_est_rise = find_b_est_rise(np.array(rise_df['Frame']), np.array(rise_df['Rise intensity']))
                            #bounds = ([0, 0], [100, 100])
                            #st.write(a_est)
                            try:
                                popt_decay, pcov_decay = curve_fit(mono_exp_decay, decay_df['Frame'], decay_df['Decay intensity'], p0=[a_est,b_est])
                                
                            except (TypeError, RuntimeError) as e:
                                error_message = str(e)
                                if error_message == "Optimal parameters not found: Number of calls to function has reached maxfev = 600":
                                    # Handle the error and continue to the next iteration
                                    continue
                                #st.write("here")
                                # Replace the error with a warning message
                                else:
                                    warning_message = "Fitting cannot be performed"
                                    warnings.warn(warning_message, category=UserWarning)
                                    popt_decay, pcov_decay = None, None
                            else: 
                                popt_decay, pcov_decay = curve_fit(mono_exp_decay, decay_df['Frame'], decay_df['Decay intensity'], p0=[a_est,b_est])
                                decay_curve_exp = mono_exp_decay(decay_df['Frame'], *popt_decay)
    
                                #st.write(popt_decay)
                            try:
                                popt_rise, pcov_rise = curve_fit(mono_exp_rise, rise_df['Frame'], rise_df['Rise intensity'], p0=[a_est_rise,b_est_rise])
                                
                            except (TypeError, RuntimeError) as e:
                                error_message = str(e)
                                if error_message == "Optimal parameters not found: Number of calls to function has reached maxfev = 600":
                                    continue
                                # Replace the error with a warning message
                                else:                           
                                    warning_message = "Fitting cannot be performed"
                                    warnings.warn(warning_message, category=UserWarning)
                                    popt_rise, pcov_rise = None, None
                                    #bounds = ([0, 0], [100, 100])
                                    #st.write(a_est)
                            else:
                                popt_rise, pcov_rise = curve_fit(mono_exp_rise, rise_df['Frame'], rise_df['Rise intensity'], p0=[a_est_rise,b_est_rise])
                                rise_curve_exp = np.round((mono_exp_rise(rise_df['Frame'], *popt_rise)),3)                

                            count_items = 0
                            for item in amp_keyval.items():
                                #st.write(item[0].split('-')) 
                                if len(item[0].split('-'))==3:
                                    count_items += 1
                                    signal_start_frame = item[0].split('-')[0]
                                    #st.write(f"The signal start frame is {int(signal_start_frame)}")
                                    peak_frame = item[0].split('-')[1]
                                    #st.write(f"The peak frame is {int(peak_frame)}")
                                    signal_decay_frame = item[0].split('-')[2]
                                    #st.write(f"The signal decay frame is {int(signal_decay_frame)}")
                                    event_num = count_items
                                    amplitude_each = item[1]
                                    signal_rise = (int(peak_frame)-int(signal_start_frame))/frame_rate
                                    signal_decay = (int(signal_decay_frame)-int(peak_frame))/frame_rate
                                    signal_duration = (int(signal_decay_frame)-int(signal_start_frame))/frame_rate
    
                                    if (popt_rise is not None) and (popt_decay is not None):
                                        nested_dict_pro["Label"].append(i)
                                        nested_dict_pro["Number of Events"].append(event_num)
                                        nested_dict_pro["Rise time"].append(signal_rise)
                                        nested_dict_pro["Decay time"].append(signal_decay)
                                        nested_dict_pro["Duration"].append(signal_duration)
                                        nested_dict_pro["Amplitude"].append(amplitude_each) 
                                        rise_rate = np.round(popt_rise[1],4)
                                        nested_dict_pro["Rise Rate"].append(rise_rate)
                                        decay_rate = np.round(popt_decay[1],4)
                                        nested_dict_pro["Decay Rate"].append(decay_rate)
                                    
                    nested_dict_final = nested_dict_pro.copy()               
                    
                    st.write('*_The original intensity data_*')  
                    st.dataframe(new_df_pro_transposed_smooth, 1000,200)
                    multi_csv_bleach = convert_df(new_df_pro_transposed_smooth)           
                    st.download_button("Press to Download",  multi_csv_bleach, 'multi_cell_data.csv', "text/csv", key='download_multi_-csv_bleach')   
                    st.write('*_The normalized Photobleaching-corrected data_*')
                    st.dataframe(plot_df_corr, 1000,200)
                    multi_csv_corr = convert_df(plot_df_corr)  
                    st.download_button("Press to Download",  multi_csv_corr, 'multi_cell_data_corr.csv', "text/csv", key='download_multi_-csv_bleach_corr')   
                    #st.write(nested_dict_final)
                    nested_dict_final = (pd.DataFrame.from_dict(nested_dict_final))
                    
                    traces_smooth_corr = []                    
                    column_new_df_corr = plot_df_corr.columns              
                    for smooth_column_corr in column_new_df_corr:    
                        if "smooth cell" in str(smooth_column_corr):
                            # create a trace for the current column
                            trace_smooth_corr = go.Scatter(x=plot_df_corr['Time'], y=plot_df_corr[smooth_column_corr], name=smooth_column_corr)
                            # add the trace to the list
                            traces_smooth_corr.append(trace_smooth_corr)
                    # create the plot
                    fig_smooth_corr = go.Figure(data=traces_smooth_corr)
                    # update the layout
                    fig_smooth_corr.update_layout(title='Corrected and Normalized Intensity Traces', xaxis_title='Time', yaxis_title='Corrected and Normalized Intensity',height=900)
                    # display the plot
                    st.plotly_chart(fig_smooth_corr, use_container_width=True)   
                    
                    if nested_dict_final.empty:
                        pass
                    else:                              
                        st.subheader("**_Parameters for selected labels_**")
                        col_7, col_8 = st.columns(2)
                        
                        with col_7: 
                            nested_dict_final = nested_dict_final[nested_dict_final.groupby('Label')['Amplitude'].transform(max) == nested_dict_final['Amplitude']]
                            nested_dict_final['Number of Events'] = nested_dict_final.groupby('Label')['Number of Events'].transform('count')
                            #nested_dict_final = nested_dict_final[(nested_dict_final['Amplitude']) == max((nested_dict_final['Amplitude']))]
                            #nested_dict_final["Number of Events"] = nested_dict_final.shape[0]
                            nested_dict_final = nested_dict_final.reset_index(drop=True)
                            st.write(nested_dict_final)  
                            all_csv_bleach = convert_df(nested_dict_final)           
                            st.download_button("Press to Download", all_csv_bleach, 'all_data.csv', "text/csv", key='all_download-csv_bleach')
                        with col_8:
                            average_rise_time = np.round(nested_dict_final['Rise time'].mean(),4)
                            st.write(f"The average rise time based on selected labels across all frames is {average_rise_time} s")
                            average_rise_rate = np.round(nested_dict_final['Rise Rate'].mean(),4)
                            st.write(f"The average rise rate based on selected labels across all frames is {average_rise_rate} per s")
                            average_decay_time = np.round(nested_dict_final['Decay time'].mean(),4)
                            st.write(f"The average decay time based on selected labels across all frames is {average_decay_time} s")
                            average_decay_rate = np.round(nested_dict_final['Decay Rate'].mean(),4)
                            st.write(f"The average decay rate based on selected labels across all frames is {average_decay_rate} per s")
                            average_duration = np.round(nested_dict_final['Duration'].mean(),4)
                            st.write(f"The average duration based on selected labels across all frames is {average_duration} s")
                            average_amplitude = np.round(nested_dict_final['Amplitude'].mean(),4)
                            st.write(f"The average amplitude based on selected labels across all frames is {average_amplitude}")

                        nested_dict_final['Amplitude'] = np.round(nested_dict_final['Amplitude'], 2)    
                        nested_dict_final['Duration'] = np.round(nested_dict_final['Duration'], 2)   
                        nested_dict_final['Decay time'] = np.round(nested_dict_final['Decay time'], 2)  
                        nested_dict_final['Rise time'] = np.round(nested_dict_final['Rise time'], 2) 
                        nested_dict_final['Rise Rate'] = np.round(nested_dict_final['Rise Rate'], 2)
                        nested_dict_final['Decay Rate'] = np.round(nested_dict_final['Decay Rate'], 2)
                        
                        exclude_columns = ['Label', 'Number of Events']
                        columns_to_plot = [col for col in nested_dict_final.columns if col not in exclude_columns]
                        
                        fig = make_subplots(rows=3, cols=2, subplot_titles = ["A", "B", "C", "D", "E", "F"])                      
                        for i, colu in enumerate(columns_to_plot):
                            row = i // 2 + 1
                            col = i % 2 + 1                            
                            fig.add_trace(go.Histogram(x=nested_dict_final[colu], name=colu, nbinsx=20, marker_line_color='black', marker_line_width=1), row=row, col=col)                                   
                        fig.update_layout(title="Histograms",height=1000, width=800, showlegend=False)
                        fig.update_xaxes(title_text="Rise time (s)", row=1, col=1)
                        fig.update_xaxes(title_text="Rise Rate (s⁻¹)", row=1, col=2)
                        fig.update_xaxes(title_text="Decay time (s)", row=2, col=1)
                        fig.update_xaxes(title_text="Decay Rate (s⁻¹)", row=2, col=2)
                        fig.update_xaxes(title_text="Duration (s)", row=3, col=1)
                        fig.update_xaxes(title_text="Amplitude", row=3, col=2)
                        fig.update_yaxes(title_text="Number of selected cells", row=1, col=1)
                        fig.update_yaxes(title_text="Number of selected cells", row=2, col=1)
                        fig.update_yaxes(title_text="Number of selected cells", row=3, col=1)
                        st.plotly_chart(fig)   
                        
                        st.warning('Navigating to another page from the sidebar will remove all selections from the current page')
                    
            if baseline_peak_selection == "Static": 
                nested_dict_final = {}           
                nested_dict_pro = {'Label':[], "Number of Events":[], "Rise time":[], "Rise Rate":[], "Decay time":[], "Decay Rate":[], "Duration":[], "Amplitude":[]}  
                baseline_recovery_frame_input = st.radio("Select one", ('Single Frame Value', 'Average Frame Value'), help='Baseline value based on a single frame, or on multiple frames')
                if baseline_recovery_frame_input ==   'Single Frame Value':                                     
                    baseline__frame_static = st.number_input("Baseline Intensity Frame number",  min_value=0, max_value=raw_img_ani_pg_2.shape[0]-1)
                elif baseline_recovery_frame_input ==   'Average Frame Value': 
                    baseline_smooth_x = st.number_input("*_Choose frame number(s) to average their corresponding intensity values for baseline calculation_*", min_value = 0, max_value = raw_img_ani_pg_2.shape[0]-1, value = 10,  key='smooth')
                    baseline__frame_static = int(sum(range(baseline_smooth_x + 1)) / (baseline_smooth_x + 1))
                    
                df_pro_pixel_remove = df_selected_1.drop(columns=df_selected.filter(regex='^Bright_pixel_area_').columns)
                #df_pro_pixel_remove = df_pro_pixel_remove.drop(columns=df_pro.filter(regex='^area').columns)
                new_df_pro_transposed_smooth = df_pro_pixel_remove.transpose()
                new_df_pro_transposed_smooth.columns = new_df_pro_transposed_smooth.iloc[0]
                new_df_pro_transposed_smooth.drop(new_df_pro_transposed_smooth.index[0], inplace=True)      
                peak__frame_static = st.number_input("Peak Intensity Frame number",  min_value=0, max_value=raw_img_ani_pg_2.shape[0]-1, value = int((raw_img_ani_pg_2.shape[0])/2)) 
                recovery_baseline__frame_static = st.number_input("Recovery Intensity Frame number",  min_value=0, max_value=raw_img_ani_pg_2.shape[0]-1, value = int(raw_img_ani_pg_2.shape[0])-1)
                if st.button("Obtain the parameters for selected labels",on_click=callback_movav_sta) or st.session_state.button_clicked_movav_sta:
                    st.warning("The parameters for all labels are obtained using the same set of selections.")
                    df_pro_pixel_remove = df_selected_1.drop(columns=df_selected.filter(regex='^Bright_pixel_area_').columns)
                    #df_pro_pixel_remove = df_pro_pixel_remove.drop(columns=df_pro.filter(regex='^area').columns)
                    new_df_pro_transposed_smooth = df_pro_pixel_remove.transpose()
                    new_df_pro_transposed_smooth.columns = new_df_pro_transposed_smooth.iloc[0]
                    new_df_pro_transposed_smooth.drop(new_df_pro_transposed_smooth.index[0], inplace=True)  
                    
                    
                    #smooth_plot_x = st.slider("*_Moving Average Window_*", min_value=1, max_value=5, help = "Select to smooth the intensity trace. Moving average of 1 would mean the original 'Mean Intensity' trace below", key = 'mov_av')
                    for i in df_selected['label']: 
                        
                        df_pro_transposed_smooth = pd.DataFrame(smooth_plot(new_df_pro_transposed_smooth[i],smooth_plot_x),columns = [f'smooth cell {i}'])
                        new_df_pro_transposed_smooth = pd.concat([new_df_pro_transposed_smooth.reset_index(drop=True), (np.round(df_pro_transposed_smooth[f'smooth cell {i}'],3)).reset_index(drop=True)],axis=1)
                        new_df_missing_values = pd.isna(new_df_pro_transposed_smooth[f"smooth cell {i}"])
                        new_df_pro_transposed_smooth.loc[new_df_missing_values, f'smooth cell {i}'] = new_df_pro_transposed_smooth.loc[new_df_missing_values, i] 
                        new_df_pro_transposed_smooth['Frame'] = pd.DataFrame(list(range(0, df_selected.shape[1])))
                        filtered_baseline_each =  new_df_pro_transposed_smooth.query("Frame == @baseline__frame_static")
                        baseline_each = filtered_baseline_each[f'smooth cell {i}'].iloc[0]                              
                        new_df_pro_transposed_smooth[f"smooth cell {i}"] = new_df_pro_transposed_smooth[f"smooth cell {i}"]/baseline_each
                    
                                        
                    new_df_pro_transposed_smooth = new_df_pro_transposed_smooth.iloc[:, [new_df_pro_transposed_smooth.shape[1] - 1] + list(range(new_df_pro_transposed_smooth.shape[1] - 1))]
                    new_df_pro_transposed_smooth['Time'] = new_df_pro_transposed_smooth['Frame']/frame_rate
     
                    plot_df_corr = pd.DataFrame()
                    plot_df_corr['Frame'] = new_df_pro_transposed_smooth['Frame']
                    plot_df_corr['Time'] = plot_df_corr['Frame']/frame_rate        
     
                    for i in df_selected['label']: 
                        
                        column_corr_first = new_df_pro_transposed_smooth.loc[(new_df_pro_transposed_smooth['Frame'] >= 0) & (new_df_pro_transposed_smooth['Frame'] <= fit_first_x), f'smooth cell {i}']
                        exp_df_1 = pd.DataFrame({f'Bleach intensity {i}': column_corr_first})
                        exp_df_1['Frames'] = new_df_pro_transposed_smooth[0:fit_first_x+1]['Frame']
                        column_corr_last = new_df_pro_transposed_smooth.loc[(new_df_pro_transposed_smooth['Frame'] >= fit_last_x) & (new_df_pro_transposed_smooth['Frame'] <= raw_img_ani_pg_2.shape[0]-1), f'smooth cell {i}']
                        exp_df_2 = pd.DataFrame({f'Bleach intensity {i}': column_corr_last})
                        exp_df_2['Frames'] = new_df_pro_transposed_smooth[fit_last_x:raw_img_ani_pg_2.shape[0]]['Frame']                   
                        exp_df = pd.concat([exp_df_1, exp_df_2], axis=0)
                        #st.write(exp_df)
                        popt_exp, pcov_exp = curve_fit(mono_exp_decay, exp_df['Frames'], exp_df[f'Bleach intensity {i}'], p0 = [np.max(exp_df['Frames']), find_b_est_decay(np.array(exp_df['Frames']), np.array(exp_df[f'Bleach intensity {i}']))])
                        photobleach_curve_exp = mono_exp_decay(new_df_pro_transposed_smooth['Frame'], *popt_exp)           
                        fit_exp_df = pd.DataFrame()
                        fit_exp_df['Frame'] = new_df_pro_transposed_smooth['Frame']
                        fit_exp_df['Photobleach Corr'] = photobleach_curve_exp
                        
                        plot_df_corr_intensity = new_df_pro_transposed_smooth[f'smooth cell {i}']-photobleach_curve_exp
                        plot_df_corr_intensity_min = min(plot_df_corr_intensity)                    
                        plot_df_corr_value = pd.DataFrame(np.round((plot_df_corr_intensity + abs(plot_df_corr_intensity_min)),3), columns = [f'smooth cell {i}'])
                        plot_df_corr = pd.concat([plot_df_corr.reset_index(drop=True), plot_df_corr_value] ,axis=1)
                        plot_df_corr.loc[plot_df_corr[f'smooth cell {i}'] == 0, f'smooth cell {i}'] = plot_df_corr[f'smooth cell {i}'].replace(0, plot_df_corr[f'smooth cell {i}'][plot_df_corr[f'smooth cell {i}'] != 0].min())
                        if baseline_recovery_frame_input ==   'Single Frame Value':                              
                            filtered_baseline_corr_each = plot_df_corr.query("Frame == @baseline__frame_static")
                            baseline_corr_each = filtered_baseline_corr_each[f'smooth cell {i}'].iloc[0]
                            #plot_df_corr[f'smooth cell {i}'] = plot_df_corr[f'smooth cell {i}']/baseline_corr_each
                            #baseline_corr_each = baseline_corr_each/baseline_corr_each                    
                            plot_df_corr[f'delta_f/f_0_{i}'] = (plot_df_corr[f'smooth cell {i}'] - baseline_corr_each)/baseline_corr_each 
                            filtered_peak_each = plot_df_corr.query("Frame == @peak__frame_static")
                            max_df_value = filtered_peak_each[f'smooth cell {i}'].iloc[0]
                            rise_df = plot_df_corr[(plot_df_corr['Frame'] >= baseline__frame_static) & (plot_df_corr['Frame'] <= peak__frame_static)]
                            decay_df = plot_df_corr[(plot_df_corr['Frame'] >= peak__frame_static) & (plot_df_corr['Frame'] <= recovery_baseline__frame_static)]
                            decay_df = decay_df[['Frame', f'smooth cell {i}']]
                            decay_df.rename(columns={f'smooth cell {i}': 'Decay intensity'}, inplace=True)
                            rise_df = rise_df[['Frame', f'smooth cell {i}']]
                            rise_df.rename(columns={f'smooth cell {i}': 'Rise intensity'}, inplace=True)   
                
                            amplitude_each = max_df_value - baseline_corr_each
                            signal_rise = (int(peak__frame_static)-int(baseline__frame_static))/frame_rate
                            signal_decay = (int(recovery_baseline__frame_static)-int(peak__frame_static))/frame_rate
                            signal_duration = (int(recovery_baseline__frame_static)-int(baseline__frame_static))/frame_rate
                            nested_dict_pro["Label"].append(i)
                            nested_dict_pro["Number of Events"].append(1)
                            nested_dict_pro["Rise time"].append(signal_rise)
                            nested_dict_pro["Decay time"].append(signal_decay)
                            nested_dict_pro["Duration"].append(signal_duration)
                            nested_dict_pro["Amplitude"].append(amplitude_each)
                            a_est_rise = rise_df['Rise intensity'].iloc[-1]
                            b_est_rise = find_b_est_rise(np.array(rise_df['Frame']), np.array(rise_df['Rise intensity']))
                            a_est = decay_df['Decay intensity'].iloc[0]
                            b_est = find_b_est_decay(np.array(decay_df['Frame']), np.array(decay_df['Decay intensity'])) 
                            
                            try:
                                popt_decay, pcov_decay = curve_fit(mono_exp_decay, decay_df['Frame'], decay_df['Decay intensity'], p0=[a_est,b_est])
                                
                            except (TypeError, RuntimeError) as e:
                                error_message = str(e)
                                if error_message == "Optimal parameters not found: Number of calls to function has reached maxfev = 600":
                                    popt_decay, pcov_decay = None, None
                                    nested_dict_pro["Decay Rate"].append(popt_decay)
                                #st.write("here")
                                # Replace the error with a warning message
                                else:
                                    warning_message = "Fitting cannot be performed"
                                    warnings.warn(warning_message, category=UserWarning)
                                    popt_decay, pcov_decay = None, None
                                    nested_dict_pro["Decay Rate"].append(popt_decay)
                            else: 
                                popt_decay, pcov_decay = curve_fit(mono_exp_decay, decay_df['Frame'], decay_df['Decay intensity'], p0=[a_est,b_est])
                                decay_curve_exp = mono_exp_decay(decay_df['Frame'], *popt_decay)
                                nested_dict_pro["Decay Rate"].append(np.round(popt_decay[1],4))
                                
                            try:
                                popt_rise, pcov_rise = curve_fit(mono_exp_rise, rise_df['Frame'], rise_df['Rise intensity'], p0=[a_est_rise,b_est_rise])
                                
                            except (TypeError, RuntimeError) as e:
                                error_message = str(e)
                                if error_message == "Optimal parameters not found: Number of calls to function has reached maxfev = 600":
                                    popt_rise, pcov_rise = None, None
                                    nested_dict_pro["Rise Rate"].append(popt_rise)
                                # Replace the error with a warning message
                                else:                           
                                    warning_message = "Fitting cannot be performed"
                                    warnings.warn(warning_message, category=UserWarning)
                                    popt_rise, pcov_rise = None, None
                                    nested_dict_pro["Rise Rate"].append(popt_rise)
                                    #bounds = ([0, 0], [100, 100])
                                    #st.write(a_est)
                            else:
                                popt_rise, pcov_rise = curve_fit(mono_exp_rise, rise_df['Frame'], rise_df['Rise intensity'], p0=[a_est_rise,b_est_rise])
                                rise_curve_exp = np.round((mono_exp_rise(rise_df['Frame'], *popt_rise)),3) 
                                nested_dict_pro["Rise Rate"].append(np.round(popt_rise[1], 4))
                            nested_dict_final = nested_dict_pro.copy()  
                            nested_dict_final = (pd.DataFrame.from_dict(nested_dict_final))                            
                            
                        elif baseline_recovery_frame_input ==  'Average Frame Value':
                            #baseline_smooth_x = st.slider("*_Choose 'n' in n(S.D.) for Smoothed Intensity trace_*", min_value = 0.0, max_value = 3.0, step = 0.1, format="%.1f", value = 1.0,help = "Slide to adjust the baseline on the 'Smoothed Mean Intensity' trace below. Baseline is calculated as: **_mode + n(S.D.)._**",  key='smooth')
                            baseline_corr_each = plot_df_corr.loc[(plot_df_corr['Frame'] >= 0) & (plot_df_corr['Frame'] <= baseline_smooth_x), f'smooth cell {i}'].mean()
                            baseline__frame_static = int(sum(range(baseline_smooth_x + 1)) / (baseline_smooth_x + 1))
                            #plot_df_corr[f'smooth cell {i}'] = plot_df_corr[f'smooth cell {i}']/baseline_corr_each
                            #baseline_corr_each = baseline_corr_each/baseline_corr_each                    
                            plot_df_corr[f'delta_f/f_0_{i}'] = (plot_df_corr[f'smooth cell {i}'] - baseline_corr_each)/baseline_corr_each 
                            filtered_peak_each = plot_df_corr.query("Frame == @peak__frame_static")
                            max_df_value = filtered_peak_each[f'smooth cell {i}'].iloc[0]
                            rise_df = plot_df_corr[(plot_df_corr['Frame'] >= baseline__frame_static) & (plot_df_corr['Frame'] <= peak__frame_static)]
                            decay_df = plot_df_corr[(plot_df_corr['Frame'] >= peak__frame_static) & (plot_df_corr['Frame'] <= recovery_baseline__frame_static)]
                            decay_df = decay_df[['Frame', f'smooth cell {i}']]
                            decay_df.rename(columns={f'smooth cell {i}': 'Decay intensity'}, inplace=True)
                            rise_df = rise_df[['Frame', f'smooth cell {i}']]
                            rise_df.rename(columns={f'smooth cell {i}': 'Rise intensity'}, inplace=True)   
                
                            amplitude_each = max_df_value - baseline_corr_each
                            signal_rise = (int(peak__frame_static)-int(baseline__frame_static))/frame_rate
                            signal_decay = (int(recovery_baseline__frame_static)-int(peak__frame_static))/frame_rate
                            signal_duration = (int(recovery_baseline__frame_static)-int(baseline__frame_static))/frame_rate
                            nested_dict_pro["Label"].append(i)
                            nested_dict_pro["Number of Events"].append(1)
                            nested_dict_pro["Rise time"].append(signal_rise)
                            nested_dict_pro["Decay time"].append(signal_decay)
                            nested_dict_pro["Duration"].append(signal_duration)
                            nested_dict_pro["Amplitude"].append(amplitude_each)
                            a_est_rise = rise_df['Rise intensity'].iloc[-1]
                            b_est_rise = find_b_est_rise(np.array(rise_df['Frame']), np.array(rise_df['Rise intensity']))
                            a_est = decay_df['Decay intensity'].iloc[0]
                            b_est = find_b_est_decay(np.array(decay_df['Frame']), np.array(decay_df['Decay intensity'])) 
                            
                            try:
                                popt_decay, pcov_decay = curve_fit(mono_exp_decay, decay_df['Frame'], decay_df['Decay intensity'], p0=[a_est,b_est])
                                
                            except (TypeError, RuntimeError) as e:
                                error_message = str(e)
                                if error_message == "Optimal parameters not found: Number of calls to function has reached maxfev = 600":
                                    popt_decay, pcov_decay = None, None
                                    nested_dict_pro["Decay Rate"].append(popt_decay)
                                #st.write("here")
                                # Replace the error with a warning message
                                else:
                                    warning_message = "Fitting cannot be performed"
                                    warnings.warn(warning_message, category=UserWarning)
                                    popt_decay, pcov_decay = None, None
                                    nested_dict_pro["Decay Rate"].append(popt_decay)
                            else: 
                                popt_decay, pcov_decay = curve_fit(mono_exp_decay, decay_df['Frame'], decay_df['Decay intensity'], p0=[a_est,b_est])
                                decay_curve_exp = mono_exp_decay(decay_df['Frame'], *popt_decay)
                                nested_dict_pro["Decay Rate"].append(np.round(popt_decay[1],4))
                                
                            try:
                                popt_rise, pcov_rise = curve_fit(mono_exp_rise, rise_df['Frame'], rise_df['Rise intensity'], p0=[a_est_rise,b_est_rise])
                                
                            except (TypeError, RuntimeError) as e:
                                error_message = str(e)
                                if error_message == "Optimal parameters not found: Number of calls to function has reached maxfev = 600":
                                    popt_rise, pcov_rise = None, None
                                    nested_dict_pro["Rise Rate"].append(popt_rise)
                                # Replace the error with a warning message
                                else:                           
                                    warning_message = "Fitting cannot be performed"
                                    warnings.warn(warning_message, category=UserWarning)
                                    popt_rise, pcov_rise = None, None
                                    nested_dict_pro["Rise Rate"].append(popt_rise)
                                    #bounds = ([0, 0], [100, 100])
                                    #st.write(a_est)
                            else:
                                popt_rise, pcov_rise = curve_fit(mono_exp_rise, rise_df['Frame'], rise_df['Rise intensity'], p0=[a_est_rise,b_est_rise])
                                rise_curve_exp = np.round((mono_exp_rise(rise_df['Frame'], *popt_rise)),3) 
                                nested_dict_pro["Rise Rate"].append(np.round(popt_rise[1], 4))
                            nested_dict_final = nested_dict_pro.copy()  
                            nested_dict_final = (pd.DataFrame.from_dict(nested_dict_final))                            
                                           
                    st.write(plot_df_corr)
                    multi_csv = convert_df(plot_df_corr)           
                    st.download_button("Press to Download",  multi_csv, 'multi_cell_data.csv', "text/csv", key='download_multi_-csv_stat_corr')                
                    #st.write(nested_dict_final)
                    nested_dict_final = (pd.DataFrame.from_dict(nested_dict_final)) 
                    traces_smooth_corr = []                    
                    column_new_df_corr = plot_df_corr.columns              
                    for smooth_column_corr in column_new_df_corr:    
                        if "smooth cell" in str(smooth_column_corr):
                            # create a trace for the current column
                            trace_smooth_corr = go.Scatter(x=plot_df_corr['Time'], y=plot_df_corr[smooth_column_corr], name=smooth_column_corr)
                            # add the trace to the list
                            traces_smooth_corr.append(trace_smooth_corr)
                    # create the plot
                    fig_smooth_corr = go.Figure(data=traces_smooth_corr)
                    # update the layout
                    fig_smooth_corr.update_layout(title='Corrected and Normalized Intensity Traces', xaxis_title='Time', yaxis_title='Corrected and Normalized Intensity',height=900)
                    # display the plot
                    st.plotly_chart(fig_smooth_corr, use_container_width=True)                       
                    if nested_dict_final.empty:
                        pass
                    else:                              
                        st.subheader("**_Parameters for selected labels_**")
                        col_7, col_8 = st.columns(2)
                        
                        with col_7: 
                            nested_dict_final = nested_dict_final[nested_dict_final.groupby('Label')['Amplitude'].transform(max) == nested_dict_final['Amplitude']]
                            nested_dict_final['Number of Events'] = nested_dict_final.groupby('Label')['Number of Events'].transform('count')
    
                            st.write(nested_dict_final)  
                            all_csv = convert_df(nested_dict_final)           
                            st.download_button("Press to Download", all_csv, 'all_data.csv', "text/csv", key='all_download-csv_corr')
                        with col_8:
                            average_rise_time = np.round(nested_dict_final['Rise time'].mean(),4)
                            st.write(f"The average rise time based on selected labels across all frames is {average_rise_time} s")
                            average_rise_rate = np.round(nested_dict_final['Rise Rate'].mean(),4)
                            st.write(f"The average rise rate based on selected labels across all frames is {average_rise_rate} per s")
                            average_decay_time = np.round(nested_dict_final['Decay time'].mean(),4)
                            st.write(f"The average decay time based on selected labels across all frames is {average_decay_time} s")
                            average_decay_rate = np.round(nested_dict_final['Decay Rate'].mean(),4)
                            st.write(f"The average decay rate based on selected labels across all frames is {average_decay_rate} per s")
                            average_duration = np.round(nested_dict_final['Duration'].mean(),4)
                            st.write(f"The average duration based on selected labels across all frames is {average_duration} s")
                            average_amplitude = np.round(nested_dict_final['Amplitude'].mean(),4)
                            st.write(f"The average amplitude based on selected labels across all frames is {average_amplitude}") 
                            
                        nested_dict_final['Amplitude'] = np.round(nested_dict_final['Amplitude'], 2)    
                        nested_dict_final['Duration'] = np.round(nested_dict_final['Duration'], 2)   
                        nested_dict_final['Decay time'] = np.round(nested_dict_final['Decay time'], 2)  
                        nested_dict_final['Rise time'] = np.round(nested_dict_final['Rise time'], 2) 
                        nested_dict_final['Rise Rate'] = np.round(nested_dict_final['Rise Rate'], 2)
                        nested_dict_final['Decay Rate'] = np.round(nested_dict_final['Decay Rate'], 2)
                        
                        exclude_columns = ['Label', 'Number of Events']
                        columns_to_plot = [col for col in nested_dict_final.columns if col not in exclude_columns]
                        
                        fig = make_subplots(rows=3, cols=2, subplot_titles = ["A", "B", "C", "D", "E", "F"])                      
                        for i, colu in enumerate(columns_to_plot):
                            row = i // 2 + 1
                            col = i % 2 + 1                            
                            fig.add_trace(go.Histogram(x=nested_dict_final[colu], name=colu, nbinsx=20, marker_line_color='black', marker_line_width=1), row=row, col=col)                                   
                        fig.update_layout(title="Histograms",height=1000, width=800, showlegend=False)
                        fig.update_xaxes(title_text="Rise time (s)", row=1, col=1)
                        fig.update_xaxes(title_text="Rise Rate (s⁻¹)", row=1, col=2)
                        fig.update_xaxes(title_text="Decay time (s)", row=2, col=1)
                        fig.update_xaxes(title_text="Decay Rate (s⁻¹)", row=2, col=2)
                        fig.update_xaxes(title_text="Duration (s)", row=3, col=1)
                        fig.update_xaxes(title_text="Amplitude", row=3, col=2)
                        fig.update_yaxes(title_text="Number of selected cells", row=1, col=1)
                        fig.update_yaxes(title_text="Number of selected cells", row=2, col=1)
                        fig.update_yaxes(title_text="Number of selected cells", row=3, col=1)
                        st.plotly_chart(fig)  
                                     
                        st.warning('Navigating to another page from the sidebar will remove all selections from the current page')
