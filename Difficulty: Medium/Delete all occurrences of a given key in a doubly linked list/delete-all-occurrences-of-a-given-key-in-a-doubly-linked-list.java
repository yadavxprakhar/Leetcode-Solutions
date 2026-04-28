/* Structure of Doubly Linked List
class Node
{
    int data;
    Node next;
    Node prev;
}*/
class Solution {
    static Node deleteAllOccurOfX(Node head, int x) {
    if(head == null || head.next == null) return null;
    Node prev = null;
    Node temp = head;
    while(temp!=null){
        if(temp.data == x){
            if(temp == head){
                head = head.next;
            }
            prev = temp.prev;
            Node nextNode = temp.next;
            if(prev != null) {
                prev.next = nextNode;
            }
            if(nextNode != null){
                nextNode.prev = prev;
            }
        }
        temp = temp.next;
    }
    return head;
    }
}