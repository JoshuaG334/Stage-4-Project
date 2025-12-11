/*
Joshua Geoghegan
12/11/2025

Open sensorData.txt file in read mode 
reads entire txt file and prints them out

*/

#include <stdio.h>

int main() {
    //Open sensorData.txt in read mode
    FILE *file = fopen("sensorData.txt", "r");

    //Check if the file opened properly
    if (file == NULL) {
        printf("Error opening sensorData.txt!\n");
        return 1;  //Exit if the file could not be opened
    }

    //Buffer to store each line as it's read
    char line[256];

    //Read lines until EOF end of file
    while (fgets(line, sizeof(line), file) != NULL) {
        //Print each line as it's read
        printf("%s", line);
    }

    //Close the file
    fclose(file);

    return 0;  //Exit
}
