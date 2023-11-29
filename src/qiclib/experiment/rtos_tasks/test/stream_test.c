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
#include <stdio.h>

#include "task.h"

int task_entry(void)
{
    // Progress should be 0

    uint32_t *param_list = (uint32_t *)rtos_GetParameters();
    uint32_t param_size_valid = rtos_GetParametersSize()/sizeof(uint32_t); // get valid parameter size

    if (param_size_valid != 2)
    {
        rtos_ReportError("Exactly two parameters are required: Length, Repetitions");
        return -1;
    }

    uint32_t length = param_list[0];
    uint32_t repetitions = param_list[1];
    rtos_printf("StreamTask: Length = %d ; Repetitions = %d\r\n", length, repetitions);

    for (int r = 0; r < repetitions; r++)
    {
        rtos_printf("Rep: %d\r\n", r);
        uint32_t *data_field = rtos_GetDataBox(length * sizeof(uint32_t));
        for (uint32_t i = 0; i < length; i++)
        {
            for (uint t = 0; t < 200000; t++)
            {

            }

            data_field[i] = length * r + i;
            rtos_SetProgress(data_field[i]);
            rtos_printf("Progress; %d\r\n", data_field[i]);
        }
        rtos_FinishDataBox(data_field);
    }
    return 42;
}
