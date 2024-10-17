package csvTest;
import java.io.BufferedReader;
import java.io.FileReader;
import java.io.IOException;

public class CsvTestRead2 {
    public static void main(String[] args) {
        String line = "";
        String splitBy = ",";

        try {
            BufferedReader br = new BufferedReader(new FileReader("./csvTest/CSVDemo.csv"));

            br.readLine(); // Skipping the header

            while ((line = br.readLine()) != null) {
                String[] person = line.split(splitBy);
                System.out.printf("Name: %s %s | Age: %s | Contact: %s | City: %s %n", person[0], person[1], person[2], person[3], person[4]);
            }
        } catch (IOException e) {
            e.printStackTrace();
        }
    }
}
