/* 
//////////////////////////////////////////////////////////////////////////////////
1
22
333
4444
55555
public class pattern4{
    public static void main(String args[]){
        int n=5;
        for(int i=1;i<=n;i++){
            for(int j=1;j<=i;j++){
                System.out.print(i);
            }
            System.out.println();
        }
    }
}
    /////////////////////////////////////////////////////////////////////////////////////////
     1   
    2 2
   3 3 3 
  4 4 4 4
 5 5 5 5 5
public class pattern4{
    public static void main(String args[]){
        int n=5;
        for(int i=1;i<=5;i++){
            for(int j=1;j<=n-i;j++){
                System.out.print(" ");
            }
            for(int j=1;j<=i;j++){
                System.out.print(i+" ");
            }
            System.out.println();
        }
    }
}

/////////////////////////////////////////////////////////////////////////////////////////////

             1
            121
           12321
          1234321
         123454321
public class pattern4{
    public static void main(String args[]){
        int n=5;
        for(int i=1;i<=n;i++){
            for(int j=1;j<=n-i;j++){
                System.out.print(" ");
            }

            for(int j=i;j>=1;j--){
                System.out.print(j);
            }

            for(int j=2;j<=i;j++){
                System.out.print(j);
            }
            System.out.println();
        }
    }
}
////////////////////////////////////////////////////////////////////////////////////////
*/

public class patterns4{
    public static void main(String args[]){
        int n=4;
        for(int i=1;i<=n;i++){
            for(int j=1;j<=n-i;j++){
                System.out.print(" ");
            }

            for(int j=1;j<=2*i-1;j++){
                System.out.print("*");
            }
        System.out.println();
        }
        for(int i=n;i>=1;i--){
            for(int j=1;j<=n-i;j++){
                System.out.print(" ");
            }

            for(int j=1;j<=2*i-1;j++){
                System.out.print("*");
            }
        System.out.println();
        }
        
        }
    }
