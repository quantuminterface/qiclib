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
#include <string.h>

#include "task.h"
#include "cells.h"

#define MAX_ADDR 1024

int task_entry(void)
{
	xil_printf("\r\nStart Quantum Jump Collection Task\r\n");

	uint32_t *param_list = (uint32_t *)rtos_GetParameters();
	uint32_t repetitions = param_list[0];

	// Fetch cell pointers from platform (do not forget to free at the end!)
	Cell *cells = cells_create();
	// Select relevant cell
	uint8_t cell_idx = 0;
	Cell cell = cells[cell_idx];

	xil_printf("Expect to collect %d states.\r\n", repetitions);

	// At the beginning we once wait until sequencer has finished possible previous task
	cells_wait_while_busy();

	//uint32_t *states = rtos_GetDataBox(repetitions >> (5 - 2)); // Divide number by 32 (states per register) and multiply by 4 (bytes per register)
	uint32_t *states = rtos_GetDataBox(sizeof(uint32_t) * (repetitions / 10)); // 3bits per state -> 10 states per reg
	for (uint32_t i = 0; i < repetitions / 10; i++)
		states[i] = 0;

	// Reset BRAM 0 and activate wrapping
	stg_set_bram_control(cell.storage, 0, true, true);
	// Record state in BRAM 0 and accumulate
	stg_set_state_config(cell.storage, 0, true, true, false);
	uint32_t *bram = stg_get_bram_pointer(cell.storage, 0);

	//rtos_printf("Current next address: %d\r\n", stg_get_next_address(cell.storage, 0));

	uint32_t last_addr = 0;
	uint32_t count = 0;
	seq_start_at(cell.sequencer, 0);
	bool busy = true;
	while (busy)
	{
		// Check sequencer here at beginning to ensure we do this loop once again if
		// sequencer finishes in the meantime (to collect remaining data)
		busy = seq_is_busy(cell.sequencer);
		uint32_t next_addr = stg_get_next_address(cell.storage, 0);
		if (next_addr < last_addr)
		{
			// Address wrapped -> collect remaining ones
			for (uint32_t i = last_addr; i < MAX_ADDR; ++i)
			{
				states[count++] = *(bram + i);
			}
			last_addr = 0; // Continue at beginning
		}
		if (next_addr > last_addr)
		{
			// More states present
			for (uint32_t i = last_addr; i < next_addr; ++i)
			{
				states[count++] = *(bram + i);
			}
			last_addr = next_addr;
		}
		rtos_SetProgress(count * 10);
		//rtos_printf("Current next address: %d\r\n", next_addr);
	}

	rtos_printf("Collected %d states!\r\n", count * 10);
	if (count * 10 < repetitions)
	{
		rtos_PrintfError(
			"Expected %d states, but only collected %d! The remaining states could not been catched in time...",
			repetitions, count * 10);
	}

	rtos_FinishDataBox(states);

	// Important to free the cells at the end to not generate a memory leak!
	cells_free(cells);
	xil_printf("\r\nTask finished.\r\n");
	return 0;
}
