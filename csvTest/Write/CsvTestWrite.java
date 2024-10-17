package csvTest.Write;

import java.io.*;

public class CsvTestWrite {
    public static void main(String[] args) throws Exception {
        FileWriter fileWriter = null;

        try {
            fileWriter = new FileWriter("./csvTest/Write/CSVDemo.csv");
            fileWriter.write("Hello");
        } catch (Exception e) {
            e.printStackTrace();
        } finally {
            try {
                if (fileWriter != null) {
                    fileWriter.flush();
                    fileWriter.close();
                }
            } catch (IOException e) {
                e.printStackTrace();
            }
        }
    }
}