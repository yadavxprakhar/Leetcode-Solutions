class Solution {

    public int shipWithinDays(int[] weights, int days) {

        int low = findMax(weights);
        int high = arrSum(weights);

        while (low <= high) {

            int mid = low + (high - low) / 2;

            int dayCnt = findDays(weights, mid);

            if (dayCnt <= days) {
                high = mid - 1;
            } else {
                low = mid + 1;
            }
        }

        return low; 
    }

    private int arrSum(int[] arr){
        int sum = 0;
        for(int i = 0; i < arr.length; i++){
            sum += arr[i];
        }
        return sum;
    }

    private int findMax(int[] arr){
        int max1 = Integer.MIN_VALUE;
        for(int i = 0; i < arr.length; i++){
            max1 = Math.max(max1, arr[i]);
        }
        return max1;
    }

    private int findDays(int[] arr, int capacity){

        int days = 1;
        int load = 0;

        for(int i = 0; i < arr.length; i++){

            if(load + arr[i] > capacity){
                days++;
                load = arr[i];
            } else {
                load += arr[i];
            }
        }

        return days;
    }
}