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
	xil_printf("\r\nStart Interleaved Qubit Experiments\r\n");

	uint32_t *param_list = (uint32_t *)rtos_GetParameters();
	uint32_t param_count = rtos_GetParametersSize() / sizeof(uint32_t);
	if (param_count < 2)
	{
		rtos_PrintfError("Not enough parameters provided (%d given).", param_count);
		return -1;
	}
	uint32_t num_of_experiments = (param_list++)[0];
	uint32_t experiments_per_loop = (param_list++)[0];

	uint32_t param_count_expected = 2						  // General parameters
									+ experiments_per_loop	  // Experiment order
									+ 3 * num_of_experiments; // Experiment-specific parameters
	if (param_count < param_count_expected)
	{
		rtos_PrintfError("Not enough parameters provided (needed atleast %d, but %d given).", param_count_expected, param_count);
		return -1;
	}
	uint32_t *experiment_order = param_list;
	param_list += experiments_per_loop;
	uint32_t *experiment_sequence_pc = param_list;
	param_list += num_of_experiments;
	uint32_t *experiment_executions = param_list;
	param_list += num_of_experiments;
	uint32_t *experiment_nco_freq = param_list;
	param_list += num_of_experiments;

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
	// Select relevant cell
	uint8_t cell_idx = 0;
	Cell cell = cells[cell_idx];

	// Data structures
	iq_pair *data[num_of_experiments];
	uint32_t pos[num_of_experiments];
	uint32_t sum_of_executions = 0;
	for (uint32_t iexp = 0; iexp < num_of_experiments; iexp++)
	{
		data[iexp] = rtos_GetDataBox(experiment_executions[iexp] * sizeof(iq_pair));
		pos[iexp] = 0;
		sum_of_executions += experiment_executions[iexp];
	}

	xil_printf("In total, perform %d experiment executions.\r\n", sum_of_executions);

	// At the beginning we once wait until controller has finished possible previous task
	cells_wait_while_busy();

	uint32_t iorder = experiments_per_loop - 1; // Initialize with last experiment in row, so by incrementing we start with the first
	uint8_t exp = 0;
	for (uint32_t i = 0; i < sum_of_executions; i++)
	{
		// xil_printf("Total execution %d / %d\r\n", i, data_total_executions);

		// Select next experiment
		// Check if next experiment still needs to be executed or if it should be skipped because no delays remain
		do
		{
			iorder = (iorder + 1) % experiments_per_loop;
			exp = experiment_order[iorder];
		} while (pos[exp] >= experiment_executions[exp]);

		// xil_printf("Execution %d / %d of experiment %d\r\n",
		// 		   current_executions[current_experiment] + 1,
		// 		   experiment_executions[current_experiment],
		// 		   current_experiment);

		// Set the NCO Frequency of the manipulation pulsegen
		pg_set_internal_frequency_reg(cell.manipulation, experiment_nco_freq[exp]);

		// Write the delay register
		seq_set_register(cell.sequencer, 1, experiment_delays[exp][pos[exp]]);
		// xil_printf("Set delay register 0 to %d tacts.\r\n", CURRENT_DELAY);

		// Start the sequencer experiment execution
		seq_start_at(cell.sequencer, experiment_sequence_pc[exp]);

		// Wait until sequencer has finished and recording module has the result
		cells_wait_while_cell_busy(cell_idx);

		// Store result in the appropriate location in the right data box
		rec_get_averaged_result(cell.recording, &data[exp][pos[exp]]);

		rtos_SetProgress(i + 1);

		// Current execution finished so increment the counter
		pos[exp]++;
	}

	for (uint32_t iexp = 0; iexp < num_of_experiments; iexp++)
	{
		rtos_FinishDataBox(data[iexp]);
	}

	// Important to free the cells at the end to not generate a memory leak!
	cells_free(cells);
	xil_printf("Task finished.\r\n");
	return 0;
}
