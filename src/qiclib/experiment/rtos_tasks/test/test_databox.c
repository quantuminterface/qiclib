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

int task_entry(void)
{
    uint32_t *param_list = (uint32_t *)rtos_GetParameters();
    uint32_t param_count = rtos_GetParametersSize() / sizeof(uint32_t);
    if (param_count != 1)
    {
        rtos_PrintfError("Please provide exactly 1 parameter value for the task (%d given).", param_count);
        return -1;
    }
    uint32_t size = param_list[0];

    void *databox = rtos_GetDataBox(size);
    // Do not put anything in there. Just need the size
    rtos_FinishDataBox(databox);

    return 0;
}
