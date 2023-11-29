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
#include "task.h"
#include "cells.h"

int task_entry()
{
    uint32_t *param_list = (uint32_t *)rtos_GetParameters();
    uint32_t param_count = rtos_GetParametersSize() / sizeof(uint32_t);
    if (param_count < 4)
    {
        rtos_PrintfError("This task needs atleast 4 parameter values (only %d given).", param_count);
        return -1;
    }
    uint32_t averages = param_list[0]; // How many repetitions to perform
    uint32_t cell_num = param_list[1]; // How many cells need to be addressed
    if (param_count != 2 + 2 * cell_num)
    {
        rtos_PrintfError("This task needs exactly %d parameter values (%d given).", 2 + 2 * cell_num, param_count);
        return -1;
    }
    uint32_t *cell_list_param = &(param_list[2]);       // The indices of the cells which should be addressed
    uint32_t *recordings = &(param_list[2 + cell_num]); // How many recordings a single sequencer execution returns for each cell

    // Verify the parameters
    uint8_t cell_list[cell_num];
    uint8_t cell_count = cells_get_count();
    for (int c = 0; c < cell_num; c++)
    {
        // Check if the cell index is valid (within range of available cells)
        if (cell_list_param[c] >= cell_count)
        {
            rtos_PrintfError(
                "Requested cell %d, but only 0 to %d available.",
                cell_list_param[c],
                cell_count - 1);
            return 1;
        }
        // Copy from 32bit to 8bit unsigned
        cell_list[c] = (uint8_t)cell_list_param[c];

        // Check if cell requests more than one recording per run (can only store one timetrace per cell)
        if (recordings[c] > 1)
        {
            rtos_PrintfError(
                "Only 1 trace can be stored within one run, but %d requested for cell %d.",
                recordings[c], cell_list[c]);
            return -1;
        }
    }

    // Fetch cell pointers from platform (do not forget to free at the end!)
    Cell *cells = cells_create();
    Cell cell[cell_num];
    uint32_t lengths[cell_num];
    for (uint32_t c = 0; c < cell_num; c++)
    {
        cell[c] = cells[cell_list[c]];

        // Get recording length for the cells
        lengths[c] = rec_get_recording_duration(cell[c].recording) << 2; // * 4 samples per cycle
        if (lengths[c] > 1024)
        {
            rtos_PrintfError(
                "Only 1024 samples can be stored within one trace, but %d requested for cell %d.",
                lengths[c], cell_list[c]);
            cells_free(cells);
            return -1;
        }
    }

    // Memory for the resulting summed up values
    //struct iq_pair_raw data_iq_raw[1024]; // Stack currently to small for this
    struct iq_pair_raw *data_iq_raw = rtos_GetDataBox(1024 * sizeof(struct iq_pair_raw));

    // Initialize the databoxes
    int32_t *sum_dataI[cell_num];
    int32_t *sum_dataQ[cell_num];
    for (int c = 0; c < cell_num; c++)
    {
        // Only create databoxes for cells where a recording was requested
        if (recordings[c] > 0)
        {
            sum_dataI[c] = rtos_GetDataBox(lengths[c] * sizeof(int32_t));
            sum_dataQ[c] = rtos_GetDataBox(lengths[c] * sizeof(int32_t));

            // Initialize both databoxes with zeros
            for (int n = 0; n < lengths[c]; n++)
            {
                sum_dataI[c][n] = 0;
                sum_dataQ[c][n] = 0;
            }
        }
    }

    // Wait for previous task to finish
    cells_wait_while_busy();

    for (int i = 0; i < averages; i++)
    {
        // Synchronously start all relevant cells
        cells_start(cell_list, cell_num);

        cells_wait_while_busy();

        // Fetch the raw timetrace memory
        for (int c = 0; c < cell_num; c++)
        {
            if (recordings[c] > 0)
            {
                rec_get_raw_timetrace(cell[c].recording, data_iq_raw, lengths[c]);
                for (int n = 0; n < lengths[c]; n++)
                {
                    sum_dataI[c][n] += data_iq_raw[n].i;
                    sum_dataQ[c][n] += data_iq_raw[n].q;
                }
            }
        }

        rtos_SetProgress(i + 1);
    }

    // Databox was only temporary -> discard it without sending back
    rtos_DiscardDataBox(data_iq_raw);

    for (int c = 0; c < cell_num; c++)
    {
        if (recordings[c] > 0)
        {
            rtos_FinishDataBox(sum_dataI[c]);
            rtos_FinishDataBox(sum_dataQ[c]);
        }
    }

    // Important to free the cells at the end to not generate a memory leak!
    cells_free(cells);
    return 0;
}
