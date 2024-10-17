package csvTest.Write;

import java.io.FileWriter;
import java.io.IOException;

public class CsvTestWrite2 {
    public static void main(String[] args) {
        try (FileWriter fileWriter = new FileWriter("./csvTest/Write/CSVDemo.csv")) {
            fileWriter.write("Hello2");
        } catch (IOException e) {
            e.printStackTrace();
        }
    }
}
