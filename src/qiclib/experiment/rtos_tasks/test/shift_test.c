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

    int32_t *param_list = (int32_t *)rtos_GetParameters();
    uint32_t param_size = rtos_GetParametersSize()/sizeof(int32_t) / 2; // get valid parameter size

    int32_t *data_field = rtos_GetDataBox(param_size * sizeof(uint32_t));
    for (uint32_t i = 0; i < param_size; i++)
    {
        data_field[i] = param_list[2 * i] >> param_list[2 * i + 1];
        rtos_SetProgress(i);
    }
    rtos_FinishDataBox(data_field);

    int32_t *data_field2 = rtos_GetDataBox(sizeof(int32_t));
    int64_t value = 0;
    int64_t *values = &value;
    for (uint32_t i = 0; i < param_size; i++)
    {
        *values += (
              (int64_t)(param_list[2 * i]) * (int64_t)(1)
        ) >> param_list[2 * i + 1];
    }
    *data_field2 = (int32_t)value;
    rtos_FinishDataBox(data_field2);

    return 42;
}
