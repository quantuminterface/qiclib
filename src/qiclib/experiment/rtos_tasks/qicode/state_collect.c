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
    uint32_t *param_list = rtos_GetParameters();
    uint32_t param_count = rtos_GetParametersSize() / sizeof(uint32_t);
    if (param_count < 4)
    {
        rtos_PrintfError("This task needs atleast 4 parameter values (only %d given).", param_count);
        return -1;
    }
    uint32_t repetitions = param_list[0]; // How many repetitions to perform
    uint32_t cell_num = param_list[1];    // How many cells need to be addressed
    if (param_count != 2 + 2 * cell_num)
    {
        rtos_PrintfError("This task needs exactly %d parameter values (%d given).", 2 + 2 * cell_num, param_count);
        return -1;
    }
    uint32_t *cell_list_param = &(param_list[2]);    // The indices of the cells which should be addressed
    uint32_t *lengths = &(param_list[2 + cell_num]); // How many values a single sequencer execution returns for each cell

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

        // Check if cell requests more memory than the BRAM of the recording module can hold
        if (lengths[c] > 1)
        {
            // Limitation by the BRAM within the recording module
            rtos_PrintfError("Only one state can currently be stored within one run per cell, but %d requested for cell %d.", lengths[c], cell_list[c]);
            return -1;
        }
    }

    // Fetch cell pointers from platform (do not forget to free at the end!)
    Cell *cells = cells_create();
    Cell cell[cell_num];
    for (uint32_t c = 0; c < cell_num; c++)
    {
        cell[c] = cells[cell_list[c]];
    }

    // Calculate how many values are required to store the states
    uint32_t values = repetitions / 10;
    if (repetitions % 10 != 0)
        ++values; // Extra value which will not be filled completely

    // Initialize the databoxes
    uint32_t *states[cell_num];
    for (int c = 0; c < cell_num; c++)
    {
        if (lengths[c] == 0)
            continue;

        states[c] = rtos_GetDataBox(sizeof(uint32_t) * values); // 3bits per state -> 10 states per reg
        for (uint32_t i = 0; i < values; i++)
            states[c][i] = 0;
    }
    // Wait for potential previous task
    cells_wait_while_busy();

    for (uint32_t i = 0; i < repetitions; i++)
    {
        // Synchronously start all relevant cells
        cells_start(cell_list, cell_num);

        cells_wait_while_busy();

        // Fetch the result memory
        for (int c = 0; c < cell_num; c++)
        {
            if (lengths[c] == 0)
                continue;

            uint8_t state = rec_get_state_result(cell[c].recording); // 3 bits
            states[c][i / 10] |= state << ((i % 10) * 3);
        }

        rtos_SetProgress(i + 1);
    }

    for (int c = 0; c < cell_num; c++)
    {
        if (lengths[c] == 0)
            continue;

        rtos_FinishDataBox(states[c]);
    }

    // Important to free the cells at the end to not generate a memory leak!
    cells_free(cells);
    return 0;
}
