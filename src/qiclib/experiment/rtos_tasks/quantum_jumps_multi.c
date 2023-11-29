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

#define MAX_ADDR 1024
#define STATES_PER_REG 32

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
    if (repetitions % STATES_PER_REG != 0)
    {
        rtos_PrintfError(
            "This task can only perform a multiple of %d repetitions (%d requested).",
            STATES_PER_REG, repetitions);
        return -1;
    }
    uint32_t cell_num = param_list[1]; // How many cells need to be addressed
    if (param_count != 2 + 2 * cell_num)
    {
        rtos_PrintfError("This task needs exactly %d parameter values (%d given).", 2 + 2 * cell_num, param_count);
        return -1;
    }
    uint32_t *cell_list_param = &(param_list[2]); // The indices of the cells which should be addressed
    // Recording counts would follow next, but not used here

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
    }

    // Fetch cell pointers from platform (do not forget to free at the end!)
    Cell *cells = cells_create();
    Cell cell[cell_num];
    for (uint32_t c = 0; c < cell_num; c++)
    {
        cell[c] = cells[cell_list[c]];

        // For each cell, initialize the storage module
        // Reset BRAM 0 and activate wrapping
        stg_set_bram_control(cell[c].storage, 0, true, true);
        // Record state in BRAM 0 and accumulate in dense mode
        stg_set_state_config(cell[c].storage, 0, true, true, true);
    }

    // Initialize the databoxes
    uint32_t *states[cell_num];
    uint32_t last_addr[cell_num];
    uint32_t count[cell_num];
    uint32_t *bram[cell_num];
    for (uint32_t c = 0; c < cell_num; c++)
    {
        states[c] = rtos_GetDataBox(sizeof(uint32_t) * (repetitions / STATES_PER_REG));
        for (uint32_t i = 0; i < repetitions / STATES_PER_REG; i++)
            states[c][i] = 0;
        last_addr[c] = 0;
        count[c] = 0;
        bram[c] = stg_get_bram_pointer(cell[c].storage, 0);
    }
    // Wait for potential previous task
    cells_wait_while_busy();

    uint32_t next_addr, i, c;

    // Synchronously start all relevant cells
    cells_start(cell_list, cell_num);
    bool busy = true;
    while (busy)
    {
        // Check busy here at beginning to ensure we do this loop once again if
        // sequencers finishe in the meantime (to collect remaining data)
        busy = cells_is_any_busy();

        for (c = 0; c < cell_num; c++)
        {
            next_addr = stg_get_next_address(cell[c].storage, 0);
            if (next_addr < last_addr[c])
            {
                // Address wrapped -> collect remaining ones
                for (i = last_addr[c]; i < MAX_ADDR; ++i)
                {
                    states[c][count[c]++] = *(bram[c] + i);
                }
                last_addr[c] = 0; // Continue at beginning
            }
            if (next_addr > last_addr[c])
            {
                // More states present
                for (i = last_addr[c]; i < next_addr; ++i)
                {
                    states[c][count[c]++] = *(bram[c] + i);
                }
                last_addr[c] = next_addr;
            }
        }
        // Take count values from first cell (the least progressed one because it is fetched first)
        rtos_SetProgress(count[0] * STATES_PER_REG);
    }

    for (c = 0; c < cell_num; c++)
    {
        if (count[c] * STATES_PER_REG < repetitions)
        {
            rtos_PrintfError(
                "Expected %d states, but only collected %d for cell %d!\n\r"
                "The remaining states could not been catched in time...",
                repetitions, count[c] * STATES_PER_REG, c);
        }

        rtos_FinishDataBox(states[c]);
    }

    // Important to free the cells at the end to not generate a memory leak!
    cells_free(cells);
    return 0;
}
