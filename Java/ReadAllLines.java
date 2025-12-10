/*
Joshua Geoghegan
12/10/2025

Open text file in read mode , reads each line in a loop 
until it reaches the end of file,
Print any error message if it occurs
*/

import java.io.BufferedReader;  //Import class to read text from files efficiently
import java.io.FileReader;      //Import class to open and read files

public class ReadAllLines {
    public static void main(String[] args) {
        try {
            //Open the file "sensorData.txt" for reading
            BufferedReader reader = new BufferedReader(new FileReader("sensorData.txt"));

            //Print a heading
            System.out.println("All lines in file:");

            //Read each line in a loop until end of file
            String line;
            while((line = reader.readLine()) != null) {
                //Print each line
                System.out.println(line);
            }

            //Close the file to release resources
            reader.close();

        } catch(Exception e) {
            //Print any error that occurs
            System.out.println("Error reading file: " + e.getMessage());
        }
    }
}
