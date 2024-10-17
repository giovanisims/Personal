package csvTest;

import java.io.FileReader;
import java.io.IOException;
import com.opencsv.CSVReader;
import com.opencsv.exceptions.CsvValidationException;
import java.util.Arrays;

public class CsvTestOpenCSV {
    public static void main(String[] args) {
        CSVReader reader = null;
        try {
            reader = new CSVReader(new FileReader("./csvTest/CSVDemo.csv"));

            // Read header
            String[] headers = reader.readNext();
            if (headers != null) {
                System.out.println(Arrays.toString(headers));
            }

            // Process data rows
            String[] nextLine;
            while ((nextLine = reader.readNext()) != null) {
                for (String token : nextLine) {
                    System.out.print(token + " ");
                }
                System.out.print("\n");
            }
        } catch (IOException | CsvValidationException e) {
            e.printStackTrace();
        } finally {
            try {
                if (reader != null) {
                    reader.close();
                }
            } catch (IOException e) {
                e.printStackTrace();
            }
        }
    }
}