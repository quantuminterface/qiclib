/* Copyright© 2017-2023 Quantum Interface (quantuminterface@ipe.kit.edu)
 * Richard Gebauer, IPE, Karlsruhe Institute of Technology
 *
 * This program is free software: you can redistribute it and/or modify
 * it under the terms of the GNU General Public License as published by
 * the Free Software Foundation, either version 3 of the License, or
 * (at your option) any later version.
 *
 * This program is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 * GNU General Public License for more details.
 *
 * You should have received a copy of the GNU General Public License
 * along with this program.  If not, see <https://www.gnu.org/licenses/>.
 */
 // Task to calculate g2 correlation function
#include "task.h"
#include "cells.h"

int task_entry()
{
    // Obtain parameters
    uint32_t *param_list = (uint32_t *)rtos_GetParameters();
    uint32_t param_count = rtos_GetParametersSize() / sizeof(uint32_t);
    if (param_count != 4)
    {
        rtos_ReportError("Please provide exactly 4 parameter values for the task.");
        return -1;
    }
    uint32_t cal_pc = param_list[0];
    uint32_t cal_averages = param_list[1];
    uint32_t cal_valueshift = param_list[2];
    uint32_t cal_recduration = param_list[3];

    uint32_t progress = 0;
    rtos_SetProgress(progress++);

    // TODO Adapt everything to run with 2 unit cells
    rtos_PrintfError("This experiment needs to be adapted for new unit cell design first!");
    return 1;

    // Use the first and second cell
    uint8_t cell_count = cells_get_count();
    if (cell_count < 2)
    {
        rtos_PrintfError("For the correlation measurements, atleast two cells are needed!");
        return 1;
    }
    Cell *cell = cells_create();

    // Create databoxes for results
    void *measure_before = rtos_GetDataBox(2 * sizeof(iq_pair));
    void *measure_after = rtos_GetDataBox(2 * sizeof(iq_pair));

    rtos_SetProgress(progress++);

    // Store current parameter temporarily - assume both recording modules are configured identically
    uint32_t old_valueshift = rec_get_value_shift(cell[0].recording);
    uint32_t old_recduration = rec_get_recording_duration(cell[0].recording);
    uint32_t old_averages = seq_get_averages(cell[0].sequencer);

    rtos_SetProgress(progress++);

    // Extract old phase offset
    uint16_t old_phaseoffset0 = rec_get_phase_offset_reg(cell[0].recording);
    uint16_t old_phaseoffset1 = rec_get_phase_offset_reg(cell[1].recording);

    rtos_SetProgress(progress++);

    // Set new values
    rec_set_value_shift(cell[0].recording, cal_valueshift);
    rec_set_value_shift(cell[1].recording, cal_valueshift);
    rec_set_recording_duration(cell[0].recording, cal_recduration);
    rec_set_recording_duration(cell[1].recording, cal_recduration);
    seq_set_averages(cell[0].sequencer, cal_averages);

    rtos_SetProgress(progress++);

    // Start calibration measurement
    seq_wait_while_busy(cell[0].sequencer);
    // TODO: With cells, one need to change the sequencer code to run on two cells -> start both here
    seq_start_at(cell[0].sequencer, cal_pc);

    rtos_SetProgress(progress++);

    // Wait until measurement finishes
    seq_wait_while_busy(cell[0].sequencer);
    rec_wait_while_busy(cell[0].recording);
    rec_wait_while_busy(cell[1].recording);

    rtos_SetProgress(progress++);

    // Fetch results from both Recording modules
    iq_pair *iq_pair_D1 = measure_before;
    iq_pair *iq_pair_D2 = measure_before + sizeof(iq_pair);
    rec_get_averaged_result(cell[0].recording, iq_pair_D1);
    rec_get_averaged_result(cell[1].recording, iq_pair_D2);

    rtos_SetProgress(progress++);

    // ASSUME: D1 is near 0°, D2 near 180° -> correct small changes
    // phi(D1) = Q(D1) / I(D1)
    // phi(D2) = -Q(D2) / -I(D2)

    // Calculate new phase offsets
    // 2pi wrap happens implicitely by the uint16_t overflowing
    uint16_t new_phaseoffset0 = old_phaseoffset0 - rec_calc_phase_offset_reg(1. * iq_pair_D1->q / iq_pair_D1->i);
    uint16_t new_phaseoffset1 = old_phaseoffset1 - rec_calc_phase_offset_reg(1. * iq_pair_D2->q / iq_pair_D2->i);

    int32_t *debug_box = rtos_GetDataBox(6 * sizeof(int32_t));
    debug_box[0] = rec_calc_phase_offset_reg(1. * iq_pair_D1->q / iq_pair_D1->i);
    debug_box[1] = rec_calc_phase_offset_reg(1. * iq_pair_D2->q / iq_pair_D2->i);
    debug_box[2] = old_phaseoffset0;
    debug_box[3] = old_phaseoffset1;
    debug_box[4] = new_phaseoffset0;
    debug_box[5] = new_phaseoffset1;

    rtos_SetProgress(progress++);

    // Set new phase offsets
    rec_set_phase_offset_reg(cell[0].recording, new_phaseoffset0);
    rec_set_phase_offset_reg(cell[1].recording, new_phaseoffset1);

    rtos_SetProgress(progress++); // 9++

    // Perform control measurement
    seq_wait_while_busy(cell[0].sequencer);
    seq_start_at(cell[0].sequencer, cal_pc);

    rtos_SetProgress(progress++);

    // Wait until measurement finishes
    seq_wait_while_busy(cell[0].sequencer);
    rec_wait_while_busy(cell[0].recording);
    rec_wait_while_busy(cell[1].recording);

    rtos_SetProgress(progress++);

    // Fetch results from both Recording modules
    iq_pair_D1 = measure_after;
    iq_pair_D2 = measure_after + sizeof(iq_pair);
    rec_get_averaged_result(cell[0].recording, iq_pair_D1);
    rec_get_averaged_result(cell[1].recording, iq_pair_D2);

    rtos_SetProgress(progress++);

    // Restore old parameters
    rec_set_value_shift(cell[0].recording, old_valueshift);
    rec_set_value_shift(cell[1].recording, old_valueshift);
    rec_set_recording_duration(cell[0].recording, old_recduration);
    rec_set_recording_duration(cell[1].recording, old_recduration);
    seq_set_averages(cell[0].sequencer, old_averages);

    rtos_SetProgress(progress++);

    // Make calibration and control measurement available for user
    rtos_FinishDataBox(measure_before);
    rtos_FinishDataBox(measure_after);
    rtos_FinishDataBox(debug_box);

    rtos_SetProgress(progress++);

    return 0;
}
