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

int task_entry()
{
	xil_printf("\r\nStart Multi Interleaved Qubit Experiments\r\n");

	uint32_t *param_list = (uint32_t *)rtos_GetParameters();
	uint32_t param_count = rtos_GetParametersSize() / sizeof(uint32_t);
	if (param_count < 3)
	{
		rtos_PrintfError("Not enough parameters provided (%d given).", param_count);
		return -1;
	}
	uint32_t num_of_experiments = (param_list++)[0];
	uint32_t experiments_per_loop = (param_list++)[0];
	uint32_t cell_num = (param_list++)[0];

	uint32_t param_count_expected = 3								 // General parameters
									+ experiments_per_loop			 // Experiment order
									+ cell_num						 // Cell map (which cells to address)
									+ num_of_experiments			 // Experiment-specific parameters
									+ num_of_experiments * cell_num; // Cell and Experiment-specific parameters
	if (param_count < param_count_expected)
	{
		rtos_PrintfError("Not enough parameters provided (needed atleast %d, but %d given).", param_count_expected, param_count);
		return -1;
	}
	uint32_t *cell_list_param = param_list;
	param_list += cell_num;
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

	uint32_t *experiment_order = param_list;
	param_list += experiments_per_loop;
	uint32_t *experiment_executions = param_list;
	param_list += num_of_experiments;
	uint32_t *experiment_nco_freq[cell_num];
	for (uint8_t c = 0; c < cell_num; c++)
	{
		experiment_nco_freq[c] = param_list;
		param_list += num_of_experiments;
	}

	for (uint32_t iexp = 0; iexp < num_of_experiments; iexp++)
		param_count_expected += experiment_executions[iexp];
	if (param_count != param_count_expected)
	{
		rtos_PrintfError("Not enough parameters provided (needed %d, but %d given).", param_count_expected, param_count);
		return -1;
	}
	uint32_t *experiment_delays[num_of_experiments];
	for (uint32_t iexp = 0; iexp < num_of_experiments; iexp++)
	{
		experiment_delays[iexp] = param_list;
		param_list += experiment_executions[iexp];
	}

	// Fetch cell pointers from platform (do not forget to free at the end!)
	Cell *cells = cells_create();
	Cell cell[cell_num];
	for (uint32_t c = 0; c < cell_num; c++)
	{
		cell[c] = cells[cell_list[c]];

		// Set start address to 0 (exp select via register)
		seq_set_start_address(cell[c].sequencer, 0);
	}

	// Data structures
	iq_pair *data[cell_num][num_of_experiments];
	uint32_t pos[num_of_experiments];
	uint32_t sum_of_executions = 0;
	for (uint32_t iexp = 0; iexp < num_of_experiments; iexp++)
	{
		for (uint32_t c = 0; c < cell_num; c++)
		{
			data[c][iexp] = rtos_GetDataBox(experiment_executions[iexp] * sizeof(iq_pair));
		}
		pos[iexp] = 0;
		sum_of_executions += experiment_executions[iexp];
	}

	xil_printf("In total, perform %d experiment executions with %d cells.\r\n", sum_of_executions, cell_num);

	// At the beginning we once wait until controller has finished possible previous task
	cells_wait_while_busy();

	uint32_t iorder = experiments_per_loop - 1; // Initialize with last experiment in row, so by incrementing we start with the first
	uint8_t exp = 0;
	for (uint32_t i = 0; i < sum_of_executions; i++)
	{
		// Select next experiment
		// Check if next experiment still needs to be executed or if it should be skipped because no delays remain
		do
		{
			iorder = (iorder + 1) % experiments_per_loop;
			exp = experiment_order[iorder];
		} while (pos[exp] >= experiment_executions[exp]);

		for (uint8_t c = 0; c < cell_num; c++)
		{
			// Set the NCO Frequency of the manipulation pulsegen
			pg_set_internal_frequency_reg(cell[c].manipulation, experiment_nco_freq[c][exp]);

			// Write the delay register
			seq_set_register(cell[c].sequencer, 1, experiment_delays[exp][pos[exp]]);
			// xil_printf("Set delay register 0 to %d tacts.\r\n", CURRENT_DELAY);

			// Write the experiment select register
			seq_set_register(cell[c].sequencer, 2, exp);
		}

		// Start the sequencer experiment execution
		cells_start(cell_list, cell_num);

		// Wait until execution finished
		cells_wait_while_busy();

		for (uint8_t c = 0; c < cell_num; c++)
		{
			// Store result in the appropriate location in the right data box
			rec_get_averaged_result(cell[c].recording, &data[c][exp][pos[exp]]);
		}

		rtos_SetProgress(i + 1);

		// Current execution finished so increment the counter
		pos[exp]++;
	}

	for (uint32_t c = 0; c < cell_num; c++)
	{
		for (uint32_t iexp = 0; iexp < num_of_experiments; iexp++)
		{
			rtos_FinishDataBox(data[c][iexp]);
		}
	}

	// Important to free the cells at the end to not generate a memory leak!
	cells_free(cells);
	xil_printf("Task finished.\r\n");
	return 0;
}
