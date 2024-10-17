package csvTest;
import java.io.*;
import java.util.Scanner;

public class CsvTestRead {
    public static void main(String[] args) throws Exception {
        Scanner csvDemo = new Scanner(new File("./csvTest/CSVDemo.csv"));
        csvDemo.useDelimiter(",");
        while (csvDemo.hasNext()){
            System.out.print(csvDemo.next());
        }
        csvDemo.close();
    }
}