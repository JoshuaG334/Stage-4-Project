/*
Joshua Geoghegan
12/11/2025

Opens text file in read mode
reads and prints the first line in the sensorData.txt file

*/

//Needed for fopen fget, and print
#include <stdio.h>

int main() {
    //Try open txt file in read mode
    //Fopen returns the file pointer * and null if it cant be opened
    FILE *file = fopen("sensorData.txt", "r");
    
    //Check if the file failed to open
    if (file == NULL) {
        printf("Error opening file!\n");
        return 1;//Exit with error code
    }
    //Create buffer to store one line from the file
    char line[256];

    //Read first line into a array
    //Stops when reaches new line .fills buffer or reaches EOF
    fgets(line, sizeof(line), file);
    //Print first line
    printf("First line: %s\n", line);
    //Close file
    fclose(file);
    
    return 0;
}
