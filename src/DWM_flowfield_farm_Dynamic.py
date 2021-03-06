"""
date: 17/07/2018
author: Augustin Grosdidier
Purpose:
Hold functions used to have a dynamic result (so, in time) in term of wake meandering, deficits
"""

import numpy as np
import matplotlib.pyplot as plt
from math import pi, sqrt, isnan
from scipy import io, interpolate
from Meandering_Main import DWM_extract_meandering_from_TurbBox
from cMann import MannBox
from Wake_added_turbulence_Main import *



def get_Meandering_dynamic(meta, meand):
    if meta.use_saved_data or meta.previous_sDWM_working_with_a_MannBox:
        # New Version for Multiple wake meandering
        meand.WakesCentersLocations_in_time = np.load(
              'C:/Users/augus/Documents/Stage/Codes/Mann_Turbulence/Result/Center_Position_in_time_Lillgrund/z_time_center_location.NPY')[meta.iT]
        # /!\ a mieux placer dans le code /!\
        meand.time = meand.WakesCentersLocations_in_time[0][:, 0]#; print 'meand time : ', meand.time
        meand.nt = len(meand.time)#; print 'number of time points: ', meand.nt

        meta.time = meand.time
        meta.nt = meand.nt

    # Change the referential to FFoR
    for i_z in np.arange(0, meta.nz, 1):
        meand.WakesCentersLocations_in_time[i_z][:, 1] = meta.hub_x[0] + meand.WakesCentersLocations_in_time[i_z][:, 1]
        meand.WakesCentersLocations_in_time[i_z][:, 2] = meta.hub_y + meand.WakesCentersLocations_in_time[i_z][:, 2]

    return meta, meand

def get_Meandering_dynamic_V2(meta, meand, TurBox, WF):
    print '# -------------------------- # DYNAMIC MEANDERING PROCESSING # ------------------------------------------- #'
    if meta.use_saved_data:
        print 'USE SAVED DATA in WAKES.NPY (pre-computed wake)'
        # New Version for Multiple wake meandering
        #meand.WakesCentersLocations_in_time = np.load(
         #     'C:/Users/augus/Documents/Stage/Codes/Mann_Turbulence/Result/Center_Position_in_time_Lillgrund/z_time_center_location.NPY')[meta.iT]
        meand.WakesCentersLocations_in_time = np.load('WAKES.NPY')[meta.iT]
        # /!\ a mieux placer dans le code /!\
        meand.time = meand.WakesCentersLocations_in_time[0][:, 0]#; print 'meand time : ', meand.time
        meand.nt = len(meand.time)#; print 'number of time points: ', meand.nt

        meta.time = meand.time
        meta.nt = meand.nt
    else:
        if meta.iT==0:
            print 'WAKES MEANDERING PROCESSING '
            WF.stream_location_z = meta.z_vec
            DWM_extract_meandering_from_TurbBox(TurBox, WF)
        print 'EXTRACT WAKES MEANDERING PROPERTIES '
        meand.WakesCentersLocations_in_time = np.load('WAKES.NPY')[meta.iT]
        meand.time = meand.WakesCentersLocations_in_time[0][:, 0]  # ; print 'meand time : ', meand.time
        meand.nt = len(meand.time)  # ; print 'number of time points: ', meand.nt

        meta.time = meand.time
        meta.nt = meand.nt

    # Change the referential to FFoR
    for i_z in np.arange(0, meta.nz, 1):
        meand.WakesCentersLocations_in_time[i_z][:, 1] = meta.hub_x[0] + meand.WakesCentersLocations_in_time[i_z][:, 1]
        meand.WakesCentersLocations_in_time[i_z][:, 2] = meta.hub_y + meand.WakesCentersLocations_in_time[i_z][:, 2]
    print '# -------------------------- # DYNAMIC MEANDERING PROCESS ENDED # ---------------------------------------- #'
    return meta, meand



def DWM_MFOR_to_FFOR_dynamic(mfor, meta, meand, ffor, MannBox):
    """
    Function that calculate the velocity in the fixed (global) frame of reference from the Mfor

    Parameters
    ----------
    meand (instance of class)   class holding the meandering parameters
    meta (instance of class)    class holding grid and ambient parameters

    Returns
    -------
    ffor (instance of class)    updated class holding global velocity field
        x_vec(1,nx) : coordinates in X direction
        y_vec(1,ny) : coordinates in Y direction
        z_vec(1,nz) : coordinates in Z direction (streamwise)
        x_mat(nx,ny): coordinates matrix in meshgrid format for the X component
        y_mat(nx,ny): coordinates matrix in meshgrid format for the Y component
        z_mat(nx,nz): coordinates matrix in meshgrid format for the Z component
        TI_meand_axial_ffor (nx,ny,nz): turbulence due to wake meandering in global coordinate system
        WS_axial_ffor (nx,ny,nz): velocity deficit in global coordinate system
        TI_axial_ffor (nx,ny,nz): apparent turbulence in global coordinate system see Madsen et al [2]
    meta (instance of class)
    """

    ##############################################################################################################
    # recalculate into Cartesian grid
    # initiate/reset Cartesian flow field
    print '# -------------------------- # MFOR to FFOR PROCESSING # ------------------------------------------------- #'
    # Some plot Check
    TEST = False
    i_z_detail = -1   # disable with a number superior to the number of WT or -1

    if meta.Meandering:
        if not meta.working_with_meandering_statistical_data:
            print 'number of time points: ', meand.nt
            DATA_from_Meandering_part = meand.WakesCentersLocations_in_time
        else:
            meand.nt = len(meand.time);
            print 'number of time points: ', meand.nt

            meta.time = meand.time
            meta.nt = meand.nt
    else:
        meta.nt = meand.nt
        print meand.nt


    print 'Performing MFoR to FFoR Computation'
    ffor.ffor_flow_field_TI_tmp_tmp = meta.TI * np.ones((meta.nx, meta.ny))  # X = lateral ,Y = vertical
    ffor.TI_axial_ffor_tmp = np.zeros((meta.nx, meta.ny, meta.nz, meta.nt))  # X = lateral ,Y = vertical, time ,Z = streamwise, t = time
    ffor.WS_axial_ffor_tmp = np.zeros((meta.nx, meta.ny, meta.nz, meta.nt))  # X = lateral ,Y = vertical, time ,Z = streamwise, t = time
    ffor.ffor_flow_field_ws_tmp2 = np.zeros((meta.nx, meta.ny, meta.nz, meta.nt))  # X = lateral ,Y = vertical, time ,Z = streamwise, t=time

    ffor.TI_meand_axial_ffor = np.zeros((meta.nx, meta.ny, meta.nz, meta.nt))
    ffor.WS_axial_ffor = np.zeros((meta.nx, meta.ny, meta.nz, meta.nt))
    ffor.WS_axial_deficit_ffor = np.zeros((meta.nx, meta.ny, meta.nz, meta.nt))
    ffor.WS_axial_added_ffor = np.zeros((meta.nx, meta.ny, meta.nz, meta.nt))
    ffor.TI_axial_ffor = np.zeros((meta.nx, meta.ny, meta.nz, meta.nt))
    ffor.TI_axial_added_ffor = np.zeros((meta.nx, meta.ny, meta.nz, meta.nt))

    ffor.x_vec_t = np.zeros((meta.nx, meta.nz))
    ffor.x_mat_t = np.zeros((meta.nx, meta.ny, meta.nz))
    # Define radial distance vectors
    # r_dist_2              = 999*np.ones((meta.nx,meta.ny))
    r_dist = 999 * np.ones((meta.nx, meta.ny, meta.nt))

    # CREATES THE GLOBAL FLOW FIELDS IN CARTESIAN GRID
    meta.x_mat = np.tile(meta.x_vec.reshape(len(meta.x_vec),1),meta.ny)
    meta.y_mat = np.tile(meta.y_vec,(meta.nx,1))
    meta.z_mat = np.tile(meta.vz, (meta.nx, 1))
    print 'meta vz: ', meta.vz

    # Store the ffor flow field
    ffor.x_vec = (meta.x_vec - meta.hub_x[0]) / 2.
    ffor.y_vec = (meta.y_vec - meta.hub_y) / 2.
    ffor.z_vec = meta.z_vec + np.hstack((0., np.cumsum(meta.hub_z[0:])))[0]
    ffor.x_mat = meta.x_mat / 2.
    ffor.y_mat = meta.y_mat / 2.
    ffor.z_mat = meta.z_mat / meta.dz
    ffor.time = meand.time

    #raw_input(ffor.x_vec)

    # --------- # Init for WaT # --------- #
    if meta.WaT:
        init_turb_WaT(MannBox, meta)
        MannBox.R_MB = (MannBox.ly / 2.) / MannBox.R_ref
        R_Mannbox = MannBox.R_MB  # recommended in Madsen, 2010, Calibration

    for i_z in np.arange(0, meta.nz, 1):

        # ------------- # Velocity/TI profil from mixL domain # ------------- #
        try:
            DWM_WS_DATA = mfor.U[meta.vz[i_z], :]

            # print 'DWM_WS_DATA: ', DWM_WS_DATA


        except:
            print 'Fatal error, possibly due to a too low turbulence intensity with respect to the demanded mean wind speed, try increase the input TI'

        if meta.Keck:
            DWM_TI_DATA = mfor.TI_DWM[meta.vz[i_z], :]

        if meta.Deficit_Process_Detail:
            plt.figure('Turbulence Intensity Correction')
            plt.plot(DWM_TI_DATA, meta.vr_mixl, label='DWM TI at WT' + str(meta.wtg_ind[i_z]))

        if meta.Keck:
            if meta.WaT:
                scale = 4.
                meta.kmt_r = (DWM_TI_DATA) / meta.mean_TI_DWM  / scale
                # meta.kmt_r = (DWM_TI_DATA - meta.mean_TI_DWM) / meta.mean_TI_DWM  # / scale
                # meta.kmt_r = (DWM_TI_DATA - meta.mean_TI_DWM)
                #print 'meant TI add:', np.mean(DWM_TI_DATA)  # - meta.mean_TI_DWM)
                if meta.WaT_detail:
                    print 'mean TI add:', np.mean(DWM_TI_DATA)  # - meta.mean_TI_DWM)
                    plt.figure()
                    plt.plot(meta.vr_mixl, meta.kmt_r)
                    plt.title('Radial scale factor based on TI from MixL')
                    plt.show()
            ### Correct DWM_TI_DATA so that no point to have lower TI than "TIamb"
            DWM_TI_DATA[DWM_TI_DATA < np.nanmean(meta.mean_TI_DWM)] = np.nanmean(meta.mean_TI_DWM)
            # print 'meta.mean_TI_DWM: ', meta.mean_TI_DWM

        if meta.Deficit_Process_Detail:
            plt.plot(DWM_TI_DATA, meta.vr_mixl, label='Corrected for TI amb')
            plt.legend()

        if meta.WaT:
            # print 'DWM_TI_DATA: ', DWM_TI_DATA
            # MADSEN Scaling for Turbulence:
            if meta.Madsen or meta.Larsen:
                Udef = DWM_WS_DATA
                # derive U by r:
                dUdef_dr_r = [0] + [(Udef[i_r + 1] - Udef[i_r - 1]) / (meta.vr_mixl[i_r + 1] - meta.vr_mixl[i_r - 1])
                                    for i_r in range(1, len(meta.vr_mixl) - 1)] + [0]

                deficit_depth = 1 - Udef
                derivative_deficit = dUdef_dr_r

                meta.kmt_r = np.abs(deficit_depth) * meta.km1 + np.abs(derivative_deficit) * meta.km2


            if TEST and False:
                if meta.WaT_detail and meta.Keck:
                    scale = 5.
                    meta.kmt_r = (DWM_TI_DATA - meta.mean_TI_DWM)#/meta.mean_TI_DWM
                    #meta.kmt_r = (DWM_TI_DATA - meta.mean_TI_DWM)
                    print 'meant TI add:', np.mean(DWM_TI_DATA - meta.mean_TI_DWM)

            if meta.WaT_detail and (meta.Larsen or meta.Madsen or meta.Keck):
                plt.figure()
                plt.title('radial scale for WaT')
                plt.plot(meta.kmt_r, meta.vr_mixl)
                plt.xlabel('[]'), plt.ylabel('[R]')
                plt.show()

        for i_t in np.arange(0, len(meand.time), 1):
            if meta.Meandering:
                if meta.working_with_meandering_statistical_data:
                    Ro_x = meand.meand_pos_x[i_z, i_t]
                    Ro_y = meand.meand_pos_y[i_z, i_t]
                else:
                    Ro_x = DATA_from_Meandering_part[i_z][i_t, 1]
                    Ro_y = DATA_from_Meandering_part[i_z][i_t, 2]
            else:
                Ro_x, Ro_y = (meta.hub_x[0], meta.hub_y)

            r_dist = np.sqrt((meta.x_mat - Ro_x) ** 2 + (meta.y_mat - Ro_y) ** 2) # Originally
            #print r_dist
            #print meta.x_mat - Ro_x


            if i_z == i_z_detail:
                plt.figure()
                plt.subplot(131)
                plt.pcolor(tmp_index_Mann_added_x)
                plt.title('tmp_index_mann_x')
                plt.subplot(132)
                plt.pcolor(tmp_index_Mann_added_y)
                plt.title('tmp_index_mann_y')
                plt.subplot(133)

                plt.pcolor(tmp_index_Mann_added)
                plt.title('tmp_index_mann')
                plt.show()

            ###############################################################
            #print 'mfor.wakeW[meta.vz[i_z]]: ', mfor.WakeW[meta.vz[i_z]]
            tmp_index = r_dist < mfor.WakeW[meta.vz[i_z]] * 1.5


            ################################################################
            tmp_field_WS = np.ones((meta.nx, meta.ny))
            tmp_field_WS[tmp_index] = np.interp(r_dist[tmp_index], meta.vr_m, DWM_WS_DATA)

            # ---------------- # Wake added Turbulence Process # ---------------------------------------------------- #
            #
            if meta.WaT:
                tmp_index_Mann_added_x = (np.abs(meta.x_mat - Ro_x) < R_Mannbox)
                tmp_index_Mann_added_y = (np.abs(meta.y_mat - Ro_y) < R_Mannbox)
                tmp_index_Mann_added = tmp_index_Mann_added_x * tmp_index_Mann_added_y
                tmp_index_added = r_dist < R_Mannbox
                # ---- # Init # ---- #
                tmp_turb = np.zeros((meta.nx, meta.ny))
                tmp_field_WS_added = np.zeros((meta.nx, meta.ny))
                Kmt_r = np.zeros((meta.nx, meta.ny))

                # ---- # Mann, Kmt_r Matrix in FFoR # ---- #
                Kmt_r[tmp_index_added] =  np.interp(r_dist[tmp_index_added], meta.vr_mixl[:-2], meta.kmt_r[:-2])
                tmp_turb[tmp_index_Mann_added] = \
                    obtain_wake_added_turbulence(MannBox, i_t, meta)(meta.x_mat-Ro_x,meta.y_mat-Ro_y)[tmp_index_Mann_added]

                # ---- # Final Component in FFoR # ---- #
                tmp_field_WS_added[tmp_index_added] = (tmp_turb*Kmt_r)[tmp_index_added]
                ffor.WS_axial_added_ffor[:, :, i_z, i_t] = tmp_field_WS_added

                if i_z == i_z_detail:
                    plt.figure()
                    plt.subplot(221)
                    plt.title('Kmt_r')
                    plt.pcolor(meta.x_mat-Ro_x, meta.y_mat-Ro_y,Kmt_r)
                    plt.colorbar()

                    plt.subplot(222)
                    plt.title('Mannbox Turb')
                    plt.pcolor( tmp_turb)
                    plt.colorbar()

                    plt.subplot(223)
                    plt.title('boolean Index')
                    plt.pcolor(tmp_index_added)

                    plt.subplot(224)
                    plt.title('added wake Turbulence')
                    plt.pcolor(tmp_field_WS_added)
                    plt.colorbar()

                    plt.show()

                    #"""

            ffor.WS_axial_deficit_ffor[:, :, i_z, i_t] = tmp_field_WS
            ffor.ffor_flow_field_ws_tmp2[:, :, i_z, i_t] = (tmp_field_WS ** 2)

            # Keck approach
            if meta.Keck:
                tmp_field_TI = meta.TI * np.ones((meta.nx, meta.ny))
                tmp_field_TI[tmp_index] = np.interp(r_dist[tmp_index], meta.vr_m, DWM_TI_DATA)

                ffor.ffor_flow_field_TI_tmp_tmp[:, :] = tmp_field_TI
                ffor.TI_axial_ffor[:, :, i_z, i_t] = ffor.ffor_flow_field_TI_tmp_tmp# ** 2

    # ------ FINAL SUMMATION in FFoR ------ #
    if not meta.WaT:
        ffor.WS_axial_ffor = ffor.WS_axial_deficit_ffor
    if meta.WaT:
        ffor.WS_axial_ffor = ffor.WS_axial_deficit_ffor + ffor.WS_axial_added_ffor

    # ------------------------ # Post Process to get TI # -------------------------------------------------------- #
    if meta.WaT:
        if False:

            mean_WS = np.mean(ffor.WS_axial_ffor, axis = (3))
            mean_WS_meand = np.mean(ffor.WS_axial_deficit_ffor, axis = (3))

            for i_t in np.arange(0, len(meand.time), 1):
                # Old Formulation
                ffor.TI_meand_axial_ffor[:, : , :, i_t] = np.sqrt((ffor.WS_axial_deficit_ffor[:, : , :, i_t]-mean_WS)**2)/mean_WS#_meand) " Orginal withou Meand
                #ffor.TI_axial_added_ffor[:, : , :, i_t] = np.abs((ffor.WS_axial_added_ffor[:, : , :, i_t]/mean_WS))
                # new Formulation
                ffor.TI_axial_added_ffor[:, :, :, i_t] = np.sqrt((ffor.WS_axial_added_ffor[:, :, :, i_t])**2.)

            #For Test
            if TEST:
                plt.figure()
                plt.subplot(121)
                plt.title('ffor.TI_axial befor post process')
                plt.contourf(ffor.TI_axial_ffor[:,:,1,0])
                plt.colorbar()
                print 'Mean TI from Keck:', np.mean(ffor.TI_axial_ffor[:,:,1,0])#-meta.mean_TI_DWM)
                print 'Mean TI from Keck in time:', np.mean(ffor.TI_axial_ffor[:, :, 1, :])#-meta.mean_TI_DWM)
                print ' Mean MEAND: ', np.mean(ffor.TI_meand_axial_ffor[:,:,0,:])
                Last_TI = ffor.TI_axial_ffor[:,:,1,0]
                MAX_TI_Keck = np.max(ffor.TI_axial_ffor[:,:,1,0])

            #Old Fomulation
            #ffor.TI_axial_ffor = np.sqrt(( ffor.TI_meand_axial_ffor + ffor.TI_axial_added_ffor) ** 2)  # +meta.mean_TI_DWM)**2)# - meta.mean_TI_DWM**2)
            ffor.TI_axial_ffor = np.sqrt(((ffor.TI_meand_axial_ffor)**2 + (ffor.TI_axial_added_ffor)**2))#+meta.mean_TI_DWM)**2)# - meta.mean_TI_DWM**2)
            ffor.TI_axial_ffor[ffor.TI_axial_ffor < meta.mean_TI_DWM] = meta.mean_TI_DWM
            if TEST:
                print 'Mean TI from Dynamic WaT at one time step:', np.mean(ffor.TI_axial_ffor[:, :, 1, 0])#-meta.mean_TI_DWM)
                print 'Mean TI from Dynamic WaT averaged in time:', np.mean(ffor.TI_axial_ffor[:, :, 1, :])#-meta.mean_TI_DWM)

                plt.subplot(122)
                plt.title('ffor.TI_axial_added')
                plt.contourf(ffor.TI_axial_added_ffor[:,:,1,0], np.linspace(0.,MAX_TI_Keck+0.05,10))#-meta.mean_TI_DWM)
                plt.colorbar()
                plt.show()
                plt.figure()
                plt.title('ffor.TI_axial')
                plt.contourf((ffor.TI_axial_ffor[:,:,0,0]-Last_TI))#/(Last_TI-meta.mean_TI_DWM))
                plt.colorbar()
                plt.show()
    if True:
        U_fluct = np.zeros((meta.nx, meta.ny, meta.nz, meta.nt))
        mean_WS = np.mean(ffor.WS_axial_ffor, axis = (3))

        for i_t in np.arange(0, len(meand.time), 1):
            U_fluct[:,:,:,i_t] = ffor.WS_axial_ffor[:,:,:,i_t] - mean_WS
        U_rms = np.sqrt(np.mean(U_fluct**2,axis=3))
        ffor.TI_axial_ffor = np.sqrt(1./3.*U_rms)
        # plt.figure()
        # plt.contourf(ffor.TI_axial_ffor[:,:,0])
        # plt.contourf(ffor.TI_axial_ffor[:, :, 2])
        # plt.colorbar()

        ffor.TI_axial_ffor[ffor.TI_axial_ffor < meta.mean_TI_DWM] = meta.mean_TI_DWM
        # plt.figure()
        # plt.contourf(ffor.TI_axial_ffor[:, :, 0])
        # plt.contourf(ffor.TI_axial_ffor[:, :, 2])
        # plt.colorbar()


    if meta.MEANDERING_plot:
        Average_TI_added = np.mean(ffor.TI_axial_added_ffor, axis = 3)
        Average_TI_meand = np.mean(ffor.TI_meand_axial_ffor, axis=3)
        Average_TI = np.mean(ffor.TI_axial_ffor, axis=3)

        X, Y = ffor.x_mat, ffor.y_mat
        ref_rotor_x_emitting = (meta.hub_x[0] + np.cos(np.linspace(-pi, pi))) / 2.
        ref_rotor_y_emitting = (meta.hub_y + np.sin(np.linspace(-pi, pi))) / 2.

        for i_z in range(meta.nz):
            ref_rotor_x_concerned = (meta.hub_x[i_z] + np.cos(np.linspace(-pi, pi))) / 2.
            ref_rotor_y_concerned = (meta.hub_y + np.sin(np.linspace(-pi, pi))) / 2.

            plt.figure(i_z)
            plt.subplot(132)
            plt.title('TI_added')
            plt.contourf(X, Y, Average_TI_added[:,:,i_z], cmap = plt.cm.jet)
            plt.plot(ref_rotor_x_emitting, ref_rotor_y_emitting, 'r', label='WT emitting')
            plt.plot(ref_rotor_x_concerned, ref_rotor_y_concerned, 'k', label='WT concerned')
            plt.colorbar()
            plt.subplot(131)
            plt.title('TI_meand')
            plt.contourf(X, Y, Average_TI_meand[:, :, i_z], cmap = plt.cm.jet)
            plt.plot(ref_rotor_x_emitting, ref_rotor_y_emitting, 'r', label='WT emitting')
            plt.plot(ref_rotor_x_concerned, ref_rotor_y_concerned, 'k', label='WT concerned')
            plt.colorbar()
            plt.subplot(133)
            plt.title('TI')
            plt.contourf(X, Y, Average_TI[:, :, i_z], cmap = plt.cm.jet)
            plt.plot(ref_rotor_x_emitting, ref_rotor_y_emitting, 'r', label='WT emitting')
            plt.plot(ref_rotor_x_concerned, ref_rotor_y_concerned, 'k', label='WT concerned')
            plt.colorbar()
        plt.show()

        Average_axial_deficit = np.mean(ffor.WS_axial_deficit_ffor, axis = 3)
        Average_added_deficit = np.mean(ffor.WS_axial_added_ffor, axis = 3)
        Average_total_deficit = np.mean(ffor.WS_axial_ffor, axis = 3)

        for i_z in range(meta.nz):
            ref_rotor_x_concerned = (meta.hub_x[i_z] + np.cos(np.linspace(-pi, pi))) / 2.
            ref_rotor_y_concerned = (meta.hub_y + np.sin(np.linspace(-pi, pi))) / 2.

            plt.figure(i_z)
            plt.subplot(132)
            plt.title('WS_axial_added')
            plt.contourf(X, Y, Average_added_deficit[:, :, i_z], cmap = plt.cm.jet)
            plt.plot(ref_rotor_x_emitting, ref_rotor_y_emitting, 'r', label='WT emitting')
            plt.plot(ref_rotor_x_concerned, ref_rotor_y_concerned, 'k', label='WT concerned')
            plt.colorbar()
            plt.subplot(131)
            plt.title('WS_axial_deficit_ffor')
            plt.contourf(X, Y, Average_axial_deficit[:, :, i_z], cmap = plt.cm.jet)
            plt.plot(ref_rotor_x_emitting, ref_rotor_y_emitting, 'r', label='WT emitting')
            plt.plot(ref_rotor_x_concerned, ref_rotor_y_concerned, 'k', label='WT concerned')
            plt.colorbar()
            plt.subplot(133)
            plt.title('WS_axial_ffor')
            plt.contourf(X, Y, Average_total_deficit[:, :, i_z], cmap = plt.cm.jet)
            plt.plot(ref_rotor_x_emitting, ref_rotor_y_emitting, 'r', label='WT emitting')
            plt.plot(ref_rotor_x_concerned, ref_rotor_y_concerned, 'k', label='WT concerned')
            plt.colorbar()
        plt.show()

    if meta.MEANDERING_plot:

        plt.ion()
        plt.figure('Meandering draw in time for each turbine in the wake')

        X, Y = ffor.x_mat, ffor.y_mat
        ref_rotor_x_emitting = (meta.hub_x[0] + np.cos(np.linspace(-pi, pi))) / 2.
        ref_rotor_y_emitting =(meta.hub_y + np.sin(np.linspace(-pi, pi))) / 2.
        #for i_z in np.arange(0, 3):
        for i_z in np.arange(1, meta.nz):
            ref_rotor_x_concerned = (meta.hub_x[i_z] + np.cos(np.linspace(-pi, pi))) / 2.
            ref_rotor_y_concerned =(meta.hub_y + np.sin(np.linspace(-pi, pi))) / 2.

            # PLOT SETTINGS
            # max_def = np.max(ffor.WS_axial_deficit_ffor[:, :, i_z, :])
            min_def = np.min(ffor.WS_axial_deficit_ffor[:, :, 0, :])

            max_added = np.max(ffor.WS_axial_added_ffor[:, :, i_z, :])
            min_added = np.min(ffor.WS_axial_added_ffor[:, :, i_z, :])


            max_tot = np.max(ffor.WS_axial_ffor[:, :, i_z, :])
            #min_tot = np.min(ffor.WS_axial_ffor[:, :, i_z, :])
            print min_def

            bar1 = np.linspace(min_def, 1., 15)
            bar2 = np.linspace(min_added, max_added, 15)
            bar3 = np.linspace(min_def, max_tot, 30)

            for i_t in np.arange(0, meand.nt, 6):
                plt.cla()
                plt.clf()
                plt.suptitle('t = '+str(ffor.time[i_t]))
                print 'i_t = ', i_t
                if meta.MEANDERING_WS_plot and not meta.MEANDERING_WS_total_plot:
                    plt.subplot(131)
                    CS1 = plt.contourf(X, Y, ffor.WS_axial_deficit_ffor[:, :, i_z, i_t], bar1, cmap = plt.cm.jet)
                    #CS1 = plt.contourf(ffor.WS_axial_deficit_ffor[:, :, i_z, i_t], bar1, cmap=plt.cm.jet)
                    plt.xlabel('x'), plt.ylabel('y'), plt.title('Axial WS FFoR for Turbine ' + str(meta.wtg_ind[i_z])) #7-iz
                    plt.plot(ref_rotor_x_emitting, ref_rotor_y_emitting, 'r', label='WT emitting')
                    plt.plot(ref_rotor_x_concerned, ref_rotor_y_concerned, 'k', label='WT concerned')
                    plt.legend()
                    plt.colorbar(CS1)
                    if meta.MEANDERING_WS_added_plot:
                        plt.subplot(132)
                        CS1 = plt.contourf(X, Y, ffor.WS_axial_added_ffor[:, :, i_z, i_t])#, bar2, cmap = plt.cm.jet)
                        #CS1 = plt.contourf(ffor.WS_axial_added_ffor[:, :, i_z, i_t], bar2, cmap=plt.cm.jet)
                        plt.xlabel('x'), plt.ylabel('y'), plt.title('Added WS FFoR for Turbine ' + str(meta.wtg_ind[i_z]))  # 7-iz
                        plt.plot(ref_rotor_x_emitting, ref_rotor_y_emitting, 'r', label='WT emitting')
                        plt.plot(ref_rotor_x_concerned, ref_rotor_y_concerned, 'k', label='WT concerned')
                        plt.legend()
                        plt.colorbar(CS1)

                        plt.subplot(133)
                        CS1 = plt.contourf(X, Y, ffor.WS_axial_ffor[:, :, i_z, i_t])#, bar3, cmap=plt.cm.jet)
                        plt.xlabel('x'), plt.ylabel('y'), plt.title(
                            'Total WS FFoR for Turbine ' + str(meta.wtg_ind[i_z]))  # 7-iz
                        plt.plot(ref_rotor_x_emitting, ref_rotor_y_emitting, 'r', label='WT emitting')
                        plt.plot(ref_rotor_x_concerned, ref_rotor_y_concerned, 'k', label='WT concerned')
                        plt.legend()
                        plt.colorbar(CS1)
                elif meta.MEANDERING_WS_total_plot:
                    CS1 = plt.contourf(X, Y, ffor.WS_axial_ffor[:, :, i_z, i_t])  # , bar3, cmap=plt.cm.jet)
                    plt.xlabel('x'), plt.ylabel('y'), plt.title(
                        'Total WS FFoR for Turbine ' + str(meta.wtg_ind[i_z]))  # 7-iz
                    plt.plot(ref_rotor_x_emitting, ref_rotor_y_emitting, 'r', label='WT emitting')
                    plt.plot(ref_rotor_x_concerned, ref_rotor_y_concerned, 'k', label='WT concerned')
                    plt.legend()
                    plt.colorbar(CS1)


                if meta.MEANDERING_TI_plot:
                    plt.subplot(122)
                    CS1 = plt.contourf(X, Y, ffor.TI_axial_ffor[:, :, i_z, i_t], 15)
                    plt.xlabel('x'), plt.ylabel('y'), plt.title('Axial TI FFoR for Turbine ' + str(meta.wtg_ind[i_z]))  # 7-iz
                    plt.plot(ref_rotor_x_emitting, ref_rotor_y_emitting, 'r', label='WT emitting')
                    plt.plot(ref_rotor_x_concerned, ref_rotor_y_concerned, 'k', label='WT concerned')
                    plt.legend()
                    plt.colorbar(CS1)

                    plt.subplot(121)
                    CS1 = plt.contourf(X, Y, ffor.TI_axial_added_ffor[:, :, i_z, i_t], 15)
                    plt.xlabel('x'), plt.ylabel('y'), plt.title('Axial TI FFoR for Turbine ' + str(meta.wtg_ind[i_z]))  # 7-iz
                    plt.plot(ref_rotor_x_emitting, ref_rotor_y_emitting, 'r', label='WT emitting')
                    plt.plot(ref_rotor_x_concerned, ref_rotor_y_concerned, 'k', label='WT concerned')
                    plt.legend()
                    plt.colorbar(CS1)

                plt.draw()
                plt.pause(0.0001)

        plt.ioff()

    print '# -------------------------- # MFOR to FFOR PROCESS ENDED # ---------------------------------------------- #'
    return mfor, ffor, meta, meand


def DWM_get_deficit_FFOR_dynamic(ffor, meta,deficits,ID_waked,inlets_ffor,inlets_ffor_deficits):
    ###############################################################
    if meta.steadyBEM_AINSLIE:
        deficits_in_time =  {}

        inlets_ffor_in_time =  {}
        inlets_ffor_deficits_in_time =  {}
        for i_z in np.arange(0, meta.nz, 1):
            deficits_in_time[str(meta.wtg_ind[i_z])] = []
            inlets_ffor_in_time[str(meta.wtg_ind[i_z])] = []
            inlets_ffor_deficits_in_time[str(meta.wtg_ind[i_z])] = []



    for i_z in np.arange(0, meta.nz, 1):
        deficits_tmp = []
        inlets_ffor_deficits_tmp = []
        inlets_ffor_tmp = []

        # on global frame mesh
        X, Y = np.meshgrid(ffor.x_vec, ffor.y_vec)
        index_trapz = np.sqrt((X + meta.C2C[i_z] / (2. * meta.WTG_spec.R)) ** 2 + (Y) ** 2) >= 0.5

        for i_t in np.arange(0, meta.nt, 1):
            wakedefmask = np.ma.array(np.squeeze(ffor.WS_axial_ffor[:, :, i_z, i_t]), mask=index_trapz,
                                      fill_value=0.0).filled()
            wakedefmasknancoarse = np.ma.array(np.squeeze(ffor.WS_axial_ffor[:, :, i_z, i_t]), mask=index_trapz,
                                               fill_value=np.nan).filled()
            disk = np.ma.array(np.zeros(wakedefmask.shape), mask=~index_trapz, fill_value=1.0).filled()
            disk_area = np.trapz(np.trapz(disk, dx=1. / meta.dy), dx=1. / meta.dx)
            trapz2 = np.trapz(np.trapz(wakedefmask, dx=1. / meta.dy), dx=1. / meta.dx)

            # on finer mesh
            # values=np.squeeze(ffor.WS_axial_ffor[:,:,i_z])
            # X, Y = np.meshgrid(ffor.x_vec,ffor.y_vec)
            # points=np.vstack((np.ravel(X),np.ravel(Y)))
            # grid_x, grid_y = np.mgrid[-0.5:0.5:meta.dR*36j, -0.5:0.5:meta.dR*36j]
            # wake_i=interpolate.griddata(points.T,np.ravel(values),(grid_x, grid_y), method='cubic')
            #
            # X2,Y2=np.meshgrid(np.linspace(-0.5,0.5,36*meta.dR),np.linspace(-0.5,0.5,36*meta.dR))
            # index_trapz=np.sqrt((X2 + meta.C2C[i_z]/(2.*meta.WTG_spec.R))**2 + (Y2)**2 )>=0.5
            #
            # wakedefmask = np.ma.array(wake_i, mask=index_trapz, fill_value=0.0).filled()
            # # wakedefmasknan = np.ma.array(wake_i, mask=index_trapz, fill_value=np.nan).filled()
            # disk = np.ma.array(np.zeros(wakedefmask.shape), mask=~index_trapz, fill_value=1.0).filled()
            # disk_area=simps(simps(disk,np.linspace(-0.5,0.5,36*meta.dR),dx=1./(36.*meta.dy)),np.linspace(-0.5,0.5,36*meta.dR),dx=1./(36.*meta.dx))
            # trapz2=simps(simps(wakedefmask,np.linspace(-0.5,0.5,36*meta.dR),dx=1./(36.*meta.dy)),np.linspace(-0.5,0.5,36*meta.dR),dx=1./(36.*meta.dx))
            #
            # COMPUTING TO PLOT

            deficits_tmp.append(trapz2 / disk_area)
            inlets_ffor_deficits_tmp.append(wakedefmasknancoarse)
            inlets_ffor_tmp.append([np.vstack(
                ((meta.x_vec - meta.hub_x[i_z]), (meta.y_vec - meta.hub_y), ffor.WS_axial_ffor[:, :, i_z, i_t]))])
            #print 'deficits_tmp: ', trapz2 / disk_area

        if meta.steadyBEM_AINSLIE:  # see meta definition in cDWM
            # think a way to save the dynamic DATA
            deficits_in_time[str(meta.wtg_ind[i_z])].append(deficits_tmp)
            inlets_ffor_deficits_in_time[str(meta.wtg_ind[i_z])].append(inlets_ffor_deficits_tmp)
            inlets_ffor_in_time[str(meta.wtg_ind[i_z])].append(inlets_ffor_tmp)
            #print 'inlets_ffor_tmp shape: ', np.shape(inlets_ffor_tmp)
            #print 'inlets_ffor_deficits_tmp shape: ', np.shape(inlets_ffor_deficits_tmp)
            # Average in time
            deficits_tmp = np.mean(deficits_tmp)
            inlets_ffor_deficits_tmp = np.mean(inlets_ffor_deficits_tmp, axis=0)
            inlets_ffor_tmp = np.mean(inlets_ffor_tmp, axis=0)
            #print 'inlets_ffor_deficits shape (after mean): ', np.shape(inlets_ffor_tmp)
            #print 'inlets_ffor_deficits_tmp shape (after mean): ', np.shape(inlets_ffor_deficits_tmp)

        # Updating

        deficits[str(meta.wtg_ind[i_z])].append(deficits_tmp)
        inlets_ffor_deficits[str(meta.wtg_ind[i_z])].append(inlets_ffor_deficits_tmp) #contained NaN value
        inlets_ffor[str(meta.wtg_ind[i_z])].append(inlets_ffor_tmp)

        ID_waked[str(meta.wtg_ind[i_z])].append(meta.wtg_ind[0])
    #"""
    if meta.DEFICIT_plot and meta.iT==7:
        if not meta.steadyBEM_AINSLIE:
            i_z = 1
            plt.figure()
            plt.title('WT' + str(i_z) + ' deficits in time')
            plt.plot(range(0, meta.nt),deficits[str(meta.wtg_ind[i_z])][0])
            plt.xlabel('Simulation time iteration, Nt'), plt.ylabel('Deficit')
            plt.show()
        if meta.steadyBEM_AINSLIE:

            # DATA in TIME
            if meta.DEFICIT_details:
                for i_z in np.arange(0, meta.nz, 1):
                    plt.figure(i_z)
                    plt.title('WT' + str(meta.wtg_ind[i_z]) + ' deficits in time')
                    plt.plot(meta.time, deficits_in_time[str(meta.wtg_ind[i_z])][-1], '-x',label='temporal data')
                    plt.plot(meta.time, [deficits[str(meta.wtg_ind[i_z])][-1] for i_t in meta.time], label='Average deficit in time')
                    plt.ylim(0., 1.)
                    plt.xlabel('Simulation time t [s]'), plt.ylabel('WS'), plt.legend()
                plt.show()

            # Averaged DATA
            plt.figure('Averaged by time Deficit')
            plt.title('Averaged Deficits generating by each Turbine on other Turbines'), plt.xlabel('WT'), plt.ylabel('Deficit')
            for i in range(len(deficits[str(0)])):
                length_ref = (len(deficits[str(0)]) - 1) + meta.nz - i
                # print 'i=', i
                # print 'length ref ', length_ref
                Deficit_to_plot = [deficits[str(i_z)][i] for i_z in np.arange(0, length_ref, 1)]
                # print Deficit_to_plot
                plt.plot(np.arange(0, length_ref, 1), Deficit_to_plot, '-x',label='WT' + str(length_ref - 1))
                if i == 0:
                    plt.xlim(length_ref - 1, 0)
            plt.legend()
            plt.show()

    return deficits, ID_waked, inlets_ffor, inlets_ffor_deficits


def DWM_get_turb_dynamic(ffor,meta,turb,inlets_ffor_turb,):
    """
    Function that calculate the rotor turbulence intensity in time
    Parameters
    ----------
    ffor:(instance of class): Instance of class Ffor holding the fixed frame of reference velocity field in global
    WF coordinates
    meta (instance of class): Instance of class Meta holding DWM core variables
    turb:  dict(nWT) holding a list of turbulence intensities contributions from upstream wakes
    inlets_ffor_turb: dict(nWT) holding a list of array containing the turbulence field in the fixed frame of reference from upstream wakes contributions at the rotor position

    Returns
    -------
    turb:  dict(nWT) updated list of turbulence intensities contributions from upstream wakes
    inlets_ffor: dict(nWT) updated list of array containing the flow field in the fixed frame of reference from upstream wakes contributions
    inlets_ffor_turb: dict(nWT) updated list of array containing the turbulence field in the fixed frame of reference from upstream wakes contributions at the rotor position
    """
    if meta.steadyBEM_AINSLIE:

        turb_in_time = {}
        inlets_ffor_turb_in_time = {}
        for i_z in np.arange(0, meta.nz, 1):
            turb_in_time[str(meta.wtg_ind[i_z])] = []
            inlets_ffor_turb_in_time[str(meta.wtg_ind[i_z])] = []
    for i_z in np.arange(0,meta.nz,1):
        X, Y = np.meshgrid(ffor.x_vec, ffor.y_vec)
        index_trapz = np.sqrt((X + meta.C2C[i_z] / (2. * meta.WTG_spec.R)) ** 2 + (Y) ** 2) >= 0.5

        turb_tmp = []
        inlets_ffor_turb_tmp =[]
        for i_t in np.arange(0, meta.nt, 1):

            turbmask = np.ma.array(np.squeeze(ffor.TI_axial_ffor[:, :, i_z, i_t]), mask=index_trapz, fill_value=0.0).filled()
            turbmasknan = np.ma.array(np.squeeze(ffor.TI_axial_ffor[:, :, i_z, i_t]), mask=index_trapz, fill_value=np.nan).filled()
            disk = np.ma.array(np.zeros(turbmask.shape), mask=~index_trapz, fill_value=1.0).filled()
            disk_area=np.trapz(np.trapz(disk,dx=1./meta.dy),dx=1./meta.dx)
            trapz2=np.trapz(np.trapz(turbmask,dx=1./meta.dy),dx=1./meta.dx)

            turb_tmp.append(trapz2/disk_area)
            inlets_ffor_turb_tmp.append(turbmasknan)

            #print 'trapz2/disk_area: ', trapz2/disk_area

        if meta.steadyBEM_AINSLIE:   # see meta definition in cDWM
            # think a way to save the dynamic DATA
            turb_in_time[str(meta.wtg_ind[i_z])].append(turb_tmp)
            inlets_ffor_turb_in_time[str(meta.wtg_ind[i_z])].append(inlets_ffor_turb_tmp)
            #print 'inlets_ffor_turb_tmp shape: ', np.shape(inlets_ffor_turb_tmp)
            # Average in time
            turb_tmpp = np.mean(turb_tmp)
            inlets_ffor_turb_tmpp = np.mean(inlets_ffor_turb_tmp, axis=0)
            #print 'inlets_ffor_turb_tmp shape (after mean): ', np.shape(inlets_ffor_turb_tmp)
        turb[str(meta.wtg_ind[i_z])].append(turb_tmpp)
        inlets_ffor_turb[str(meta.wtg_ind[i_z])].append(inlets_ffor_turb_tmpp)

    #PLOTTING
    if meta.DEFICIT_plot:
        if not meta.steadyBEM_AINSLIE:
            i_z = 1
            plt.figure()
            plt.title('WT' + str(i_z) + ' Axial TI in time')
            plt.plot(meta.time,turb[str(meta.wtg_ind[i_z])][0])
            plt.xlabel('Simulation time t [s]'), plt.ylabel('Axial TI')
            plt.show()
        if meta.steadyBEM_AINSLIE:

            # DATA in TIME
            if meta.DEFICIT_details:
                for i_z in np.arange(0, meta.nz, 1):
                    plt.figure(i_z)
                    plt.title('WT' + str(meta.wtg_ind[i_z]) + ' Axial TI in time')
                    plt.plot(meta.time, turb_in_time[str(meta.wtg_ind[i_z])][-1], label='temporal data')
                    plt.plot(meta.time, [turb[str(meta.wtg_ind[i_z])][-1] for i_t in meta.time], label='Average Axial TI in time')
                    plt.ylim(0., .2)
                    plt.xlabel('Simulation time t [s]'), plt.ylabel('Axial TI'), plt.legend()
                plt.show()

            # Averaged DATA
            plt.figure('Axial TI Averaged by time')
            plt.title('Axial TI Averaged generating by each Turbine on other Turbines'), plt.xlabel('WT'), plt.ylabel('Axial TI')
            for i in range(len(turb[str(0)])):
                length_ref = (len(turb[str(0)]) - 1) + meta.nz - i
                # print 'i=', i
                # print 'length ref ', length_ref
                Deficit_to_plot = [turb[str(i_z)][i] for i_z in np.arange(0, length_ref, 1)]
                # print Deficit_to_plot
                plt.plot(np.arange(0, length_ref, 1), Deficit_to_plot, label='WT' + str(length_ref - 1))
                if i == 0:
                    plt.xlim(length_ref - 1, 0)
            plt.legend()
            #print 'turb: ', turb
            plt.show()
    return turb,inlets_ffor_turb


def DWM_aero_steady(meta,ffor,aero,deficits,turb,inlets_ffor,inlets_ffor_deficits,out,ID_waked):
    """ Aerodynamique module of the DWM. This module contains the wake summation module (deficit and turbulence accumulation)
    The steady state blade element momentum

        Inputs
        ----------
        meta (instance of class): Instance of class Meta holding DWM core variables
        aero (instance of class): Instance of class Aero holding BEM-aero core variables

        deficits: dict(nWT) holding a list of deficits contributions from upstream wakes
        turb:  dict(nWT) holding a list of mean turbulence intensities contributions from upstream wakes
        inlets_ffor: dict(nWT) holding a list of array containing the flow field in the fixed frame of reference from
        upstream wakes contributions
        inlets_ffor_deficits: dict(nWT) holding a list of array containing the flow field in the fixed frame of
        reference from upstream wakes contributions at the rotor position
        out: dict(nWT),holding the main sDWM model outputs i.e mean power from BEM, mean power estimated from powercurve,
        mean rotor averaged wind speed, mean rotor average turbulence intensity, mean thrust coefficient from BEM and
        from power curve

        Outputs
        ----------
        aero (instance of class): updated Instance of class Aero holding BEM-aero core variables
        mfor (instance of class): updated Instance of class Mfor holding the meandering frame of reference scalars used by the Ainslie model
        out dict(nWT): dict including mean power from PC and BEM, mean thrust coefficient from PC and BEM
        BEM (instance of class): holds the key results from the BEM calculation

    """
    mfor   =  MFoR(meta.WTG)
    ## Compute the average wake deficit accumulation

    if meta.wake_ind_setting == 1:
        meta.mean_WS_DWM = []
        Deficits_in_time = deficits.get(str(meta.wtg_ind[0]))  # we get the deficit of the generating plan for the current WT
        print 'Deficits_in_time for the current WT: ', Deficits_in_time
        if not Deficits_in_time: # means that the current turbine is in free stream (first Turbine in the row)
            nt=1  # for the first Turbine in the free stream, there is no temporal iteration

        else:
            nt=meta.nt
            Deficits_in_time = np.array(Deficits_in_time)
        print 'Deficits_in_time for the current WT: ', Deficits_in_time
        print 'Deficits_in_time for the current WT shape: ', np.shape(Deficits_in_time)
        raw_input('Press Enter to continue')
        for i_t in np.arange(0, nt, 1):
            if nt == 1:   # means that the current turbine is in free stream (first Turbine in the row)
                rWS = np.array([1.0])
            else :
                rWS = Deficits_in_time[:, i_t]
            print 'deficit of the generating plan for the current WT at a certain time: ', rWS

            if meta.accu == 'linear':
                meta.mean_WS_DWM.append(meta.WS*(1.-(np.sum([1. - xx for xx in rWS]))))
            elif meta.accu == 'quadratic':
                meta.mean_WS_DWM.append(meta.WS*(1.-np.sqrt(np.sum([(1.-xx)**2 for xx in rWS]))))
            elif meta.accu == 'dominant':
                meta.mean_WS_DWM.append(meta.WS*(1.-(np.max([1. - xx for xx in rWS]))))
                # meta.mean_WS_DWM= meta.WS*(1.-(np.max([1. - xx for xx in rWS])))
            # elif meta.accu == 'bypassed':
            #     meta.mean_WS_DWM= meta.WS
            elif meta.accu == 'ewma':
                print 'This model is currently being developped and implemented soon'
            else:
                print 'You have not specified any wake accumulation procedure... or mispelled it. Options are ''linear'', ''quadratic'' , ''dominant'' or ''ewma'''
    else:
        meta.mean_WS_DWM   = meta.WS # free stream everywhere similar to current implementation of HAWC2
    meta.mean_WS_DWM = np.array(meta.mean_WS_DWM)
    print 'meta.mean_WS_DWM: ', meta.mean_WS_DWM
    # Set buildup of turbulence
    if meta.Tbuildup_setting==1:
        ti = turb.get(str(meta.wtg_ind[0]))

        Turb_in_time = deficits.get(str(meta.wtg_ind[0]))  # we get the deficit of the generating plan for the current WT
        print 'Turb_in_time for the current WT: ', Turb_in_time
        if not Turb_in_time:  # means that the current turbine is in free stream (first Turbine in the row)
            nt = 1  # for the first Turbine in the free stream, there is no temporal iteration

        else:
            nt = meta.nt
            Turb_in_time = np.array(Turb_in_time)
        print 'Turb_in_time for the current WT: ', Turb_in_time
        print 'Turb_in_time for the current WT shape: ', np.shape(Turb_in_time)
        raw_input('Press Enter to continue')
        for i_t in np.arange(0, nt, 1):

            if nt == 1:
                meta.mean_TI_DWM  = meta.TI
            else:
                meta.mean_TI_DWM  = np.max(Turb_in_time[:, i_t])
    else:
        meta.mean_TI_DWM  = meta.TI

    meta.mean_TI_DWM = np.array(meta.mean_WS_DWM)
    print 'meta.mean_TI_DWM: ', meta.mean_TI_DWM

    raw_input('Run BEM at accumulated deficit')
    # Run BEM at accumulated deficit
    aero,BEM   =  DWM_rotor_aero(meta,aero,ID_waked)

    # domain induction
    a_domain     = np.interp(meta.vr_m,np.hstack(([aero.r_w, aero.r_w[-1]+0.01, aero.r_w[-1]+0.02])), np.hstack((( 1.0 - aero.U_w), [0., 0.])))

    ## Compute the accumulated flow field for accurate inlet definition of the MFoR wake calculation
    # center all disks before wake accumulation
    if not inlets_ffor.get(str(meta.wtg_ind[0])):# if turbine in FREESTREAM, then mfor.Uinit is initialized in the calc_mixL module
        # mfor.U_init =   None # set to none for further initialization
        radial=np.hstack((aero.r_w[0:-2],aero.r_w.max(0)+0.01,meta.vr_mixl[-1]))
        vel=np.hstack((aero.U_w[0:-2],0.99, 1.))
        f3=interpolate.InterpolatedUnivariateSpline(radial,vel,  k=1)
        mfor.U_init=f3(meta.vr_mixl)
        mfor.U_init=smooth( mfor.U_init,window_len=5)
    elif meta.accu_inlet is False:
        # mfor.U_init =   None
        radial=np.hstack((aero.r_w[0:-2],aero.r_w.max(0)+0.01,meta.vr_mixl[-1]))
        vel=np.hstack((aero.U_w[0:-2],0.99, 1.))
        f3=interpolate.InterpolatedUnivariateSpline(radial,vel,  k=1)
        mfor.U_init=f3(meta.vr_mixl)
        mfor.U_init=smooth( mfor.U_init,window_len=5)
    else:   # if turbine not in the freestream, we need to compute the proper accumulated inlet to the turbine
        ranger=np.linspace(-1.,1.,meta.dR*2.)  # np.linspace(-2.,2.,meta.dR*4.)
        inlets_ffor_deficits_np_3D=np.ones((len(ranger) ,len(ranger)   , len(inlets_ffor[str(meta.wtg_ind[0])])))
        # grid_x, grid_y = np.mgrid[-1.:1.:meta.dR*2j, -1.:1.:meta.dR*2j]
        grid_x, grid_y = np.mgrid[-1.:1.:meta.dR*2j, -1.:1.:meta.dR*2j]
        for ii in range(len(inlets_ffor[str(meta.wtg_ind[0])])):
            offsets=2.*(min(inlets_ffor[str(meta.wtg_ind[0])][ii][0][0])+abs(max(inlets_ffor[str(meta.wtg_ind[0])][ii][0][0])-min(inlets_ffor[str(meta.wtg_ind[0])][ii][0][0]))/2.)
            # need to interp on a new array of equal size
            values=inlets_ffor_deficits[str(meta.wtg_ind[0])][ii]
            X, Y = np.meshgrid(inlets_ffor[str(meta.wtg_ind[0])][ii][0][0]-offsets,inlets_ffor[str(meta.wtg_ind[0])][ii][0][1])
            points=np.vstack((np.ravel(X),np.ravel(Y)))
            # wake_i=interpolate.griddata(points.T,np.ravel(values),(grid_x, grid_y), method='linear')
            wake_i=interpolate.griddata(points.T,np.ravel(values),(grid_x, grid_y), method='linear')
            inlets_ffor_deficits_np_3D[:,:,ii]=wake_i
            # print wake_i
        if meta.accu == 'linear':
            U_init=1.-(np.sum(1.-inlets_ffor_deficits_np_3D,axis=2))
        elif meta.accu == 'quadratic':
            U_init=1.-np.sqrt(np.sum((1.-inlets_ffor_deficits_np_3D)**2,axis=2))
        elif meta.accu == 'dominant':
            U_init=np.amin(inlets_ffor_deficits_np_3D, axis=2)
        elif meta.accu == 'ewma':
            print 'This model is currently being developped and implemented soon'
        else:
            print 'You have not specified any wake accumulation procedure... or mispelled it. Options are ''linear'', ''quadratic'' , ''dominant'' or ''ewma'''
        # Transform to axisymmetric profile inlet
        r_dist_2= np.sqrt(grid_x**2 + grid_y**2 )  #Find distance to centre of wake plane
        ffor.WS_axial_sym      = np.ones((len(np.arange(0,meta.dR+1.,1))))
        ffor.WS_axial_sym[0]=np.nanmean(U_init[r_dist_2 < (1.05*np.amin(r_dist_2))])
        print 'meta.dR: ', meta.dR
        for i_r_pos in np.arange(1,meta.dR+1,1):
            print 'i_r_pos: ', i_r_pos
            a=r_dist_2 > ((i_r_pos+1-1.5)*(1.0/meta.dR))# rotor neg boundaries
            bb=r_dist_2 < ((i_r_pos+1-0.5)*(1.0/meta.dR)) #rotor pos boundaries
            c=np.logical_and(a,bb)
            bin_filter = c
            tmp_ffor_flow_field_ws_mean          = U_init[bin_filter]
            ffor.WS_axial_sym[i_r_pos]           = np.nanmean(tmp_ffor_flow_field_ws_mean)
        ffor.r_sym=np.arange(0,meta.dR+1.,1)/meta.dR
        # Update the DWM inlet
        if ffor.r_sym[-1] >= meta.vr_mixl[-1]:
            # mfor.U_init = (1.0-a_domain) * np.interp(meta.vr_mixl,ffor.r_sym,ffor.WS_axial_sym)
            print 'spline interpolation'
            mfor.U_init = (1.0-a_domain) * interpolate.InterpolatedUnivariateSpline(meta.vr_mixl,ffor.r_sym,ffor.WS_axial_sym)
        else:
            print 'meta.lr_mixl: ', meta.lr_mixl
            mfor.U_init = (1.0-a_domain) * np.hstack((ffor.WS_axial_sym.ravel(), np.ones((((meta.dR * int(meta.lr_mixl))-ffor.WS_axial_sym.size),1)).ravel()))
        # Finishing
        mfor.U_init_raw=mfor.U_init
        mfor.U_init[mfor.U_init < 0.0]=0.0 # prevent from negative velocities on linear summation
        mfor.U_init=smooth( mfor.U_init,window_len=5)

    # Power curve based
    try:
        if BEM.derated is False:
            # print 'use standard ws for curve'
            aero.pow_cur=meta.WTG_spec.get_P(meta.mean_WS_DWM)
            aero.ct_cur=meta.WTG_spec.get_CT(meta.mean_WS_DWM)
        else:
            # print 'use demanded ws for curve'
            aero.pow_cur=meta.WTG_spec.get_P(BEM.Ud)
            aero.ct_cur=meta.WTG_spec.get_CT(BEM.Ud)
    except:
        aero.pow_cur=0.
        aero.ct_cur=0.
    # write outlets

    #/!\/!\ not put in commentary this  /!\/!\
    """
    out[str(meta.wtg_ind[0])]=[]
    out[str(meta.wtg_ind[0])].append(float(format(aero.Power/1000., '.2f')))
    out[str(meta.wtg_ind[0])].append(float(format(meta.mean_WS_DWM, '.2f')))
    out[str(meta.wtg_ind[0])].append(float(format(meta.mean_TI_DWM, '.2f')))
    out[str(meta.wtg_ind[0])].append(float(format(aero.CT/1., '.2f')))
    out[str(meta.wtg_ind[0])].append(float(format(aero.pow_cur, '.2f'))) # based on power curve
    out[str(meta.wtg_ind[0])].append(float(format(aero.ct_cur, '.2f'))) # based on power curve
    #"""
    return aero, mfor, out, BEM