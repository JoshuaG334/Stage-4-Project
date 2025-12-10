/*
Joshua Geoghegan
12/10/2025

Open .txt file in read mode, read the first line and 
Print to console, if not print error message
*/

import java.io.BufferedReader;  //Import class to read text from files efficiently
import java.io.FileReader;      //Import class to open and read files

public class ReadFirstLine {
    public static void main(String[] args) {
        try {
            //Open the file named "sensorData.txt" for reading
            BufferedReader reader = new BufferedReader(new FileReader("sensorData.txt"));

            //Read the first line of the file
            String line = reader.readLine();

            //Check if the line is not null, file might be empty
            if(line != null) {
                //Print the first line to the console
                System.out.println("First line: " + line);
            } else {
                //Print a message if the file is empty
                System.out.println("File is empty.");
            }

            //Close the file to release resources
            reader.close();

        } catch(Exception e) {
            //Print any error that occurs while opening/reading the file
            System.out.println("Error reading file: " + e.getMessage());
        }
    }
}
