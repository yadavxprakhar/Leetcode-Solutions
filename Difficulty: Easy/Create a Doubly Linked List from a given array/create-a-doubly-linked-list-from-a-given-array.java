/*
class Node {
    int data;
    Node next;
    Node prev;

    Node(int d) {
        data = d;
        next = null;
        prev = null;
    }
}
*/

class Solution {
    public Node createDLL(int arr[]) {
        if(arr.length == 0) return null;
        Node head = new Node(arr[0]);
        Node prev = head;
        for(int i=1; i<arr.length; i++){
            Node temp = new Node(arr[i]);
            temp.prev = prev;
            prev.next = temp;
            prev = temp;
        }
        return head;
    }
}