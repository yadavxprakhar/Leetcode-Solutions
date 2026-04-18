/*
class Node
{
    int data;
    Node next;
    Node prev;
    Node(int data)
    {
        this.data = data;
        next = prev = null;
    }
}
*/

class Solution {
    Node insertAtPos(Node head, int p, int x) {
        Node newNode = new Node(x);
        if (head == null) return newNode;
        Node temp = head;
        int cnt = 0;
        while (temp != null && cnt < p) {
            temp = temp.next;
            cnt++;
        }
        if (temp == null) return head;
        Node front = temp.next;
        newNode.next = front;
        newNode.prev = temp;
        temp.next = newNode;
        if (front != null) {
            front.prev = newNode;
        }
        return head;
    }
}