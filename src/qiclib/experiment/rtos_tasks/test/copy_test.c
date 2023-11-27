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
    //rtos_ReportError("Hallo123");
    //rtos_ReportError("Hallo123Hallo123Hallo123Hallo123Hallo123Hallo123Hallo123Hallo123Hallo123Hallo123Hallo123Hallo123Hallo123Hallo123Hallo123Hallo123Hallo123Hallo123Hallo123Hallo123Hallo123Hallo123");
    uint32_t *param_list = (uint32_t *)rtos_GetParameters();
    uint32_t param_size_valid = rtos_GetParametersSize()/sizeof(uint32_t); // get valid parameter size
    rtos_printf("[TASK] param_size_valid=%d\r\n", param_size_valid);

    uint32_t *data_field_params = rtos_GetDataBox(param_size_valid * sizeof(uint32_t));
    for (uint32_t i = 0; i < param_size_valid; i++)
    {
        //rtos_printf("param%d=%d, ", i, *(param_list));
        data_field_params[i] = param_list[i];
        rtos_SetProgress(i);
    }

    rtos_printf("\r\n");
    //rtos_PrintfError("Param_list: adr=0x%x size=%d", (unsigned int) data_field_params, (unsigned int) (param_size_valid * sizeof(uint32_t)));
    rtos_FinishDataBox(data_field_params);

    //testblock for multiple open databoxes and diffrent formats
    #define DATA_FIELD_LENGTH 3
    int8_t *data_field_INT8 = rtos_GetDataBox(DATA_FIELD_LENGTH*sizeof(int8_t));
    int16_t *data_field_INT16 = rtos_GetDataBox(DATA_FIELD_LENGTH*sizeof(int16_t));
    int32_t *data_field_INT32 = rtos_GetDataBox(DATA_FIELD_LENGTH*sizeof(int32_t));
    int64_t *data_field_INT64 = rtos_GetDataBox(DATA_FIELD_LENGTH*sizeof(int64_t));

    for(uint32_t i = 0; i < DATA_FIELD_LENGTH; i++){
        data_field_INT8[i]  = 0x77;
        data_field_INT16[i] = 0x7777;
        data_field_INT32[i] = 0x77777777;
        data_field_INT64[i] = 0x7777777777777777;

    }
    rtos_FinishDataBox(data_field_INT8);
    rtos_FinishDataBox(data_field_INT16);
    rtos_FinishDataBox(data_field_INT32);
    rtos_FinishDataBox(data_field_INT64);

    // check if memory is freed, when not discarded
    uint8_t *data_field5 = rtos_GetDataBox(1024);
    memset(data_field5, 0xAA, 1024);


    // Try big databox
    //rtos_ReportError("Allocate second big databox and fill with 123456789");
    int big_databox_size = 0x8000000;
    uint32_t * data_field_big = rtos_GetDataBox(big_databox_size);
    for (uint32_t i = 0; i < big_databox_size/sizeof(uint32_t); i++){
        data_field_big[i] = 123456789;
        rtos_SetProgress(i);
    }
    rtos_FinishDataBox(data_field_big);
    //rtos_PrintfError("Databox filled with 123456789: adr=0x%x size=%d", (unsigned int) data_field_big, big_databox_size);

    /* Check float, double and long long int support */
    float x = 345.45;
    double y = 98274.45;
    y = x*y;
    long long int long_zahl = 92472974294729;
    rtos_printf("Zahl: %d",(int) y);
    rtos_printf("Zahl: %d", long_zahl);


    return 42;
}
