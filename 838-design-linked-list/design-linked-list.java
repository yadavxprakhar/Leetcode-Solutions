class MyLinkedList {

    class Node {
        int data;
        Node next;

        Node(int data) {
            this.data = data;
            this.next = null;
        }
    }

    Node head;

    public MyLinkedList() {
        head = null;
    }

    public int get(int index) {
        Node temp = head;
        int count = 0;

        while (temp != null) {
            if (count == index) return temp.data;
            count++;
            temp = temp.next;
        }
        return -1;
    }

    public void addAtHead(int val) {
        Node node = new Node(val);
        node.next = head;
        head = node;
    }

    public void addAtTail(int val) {
        Node node = new Node(val);

        if (head == null) {
            head = node;
            return;
        }

        Node temp = head;
        while (temp.next != null) {
            temp = temp.next;
        }

        temp.next = node;
    }

    public void addAtIndex(int index, int val) {

        if (index == 0) {
            addAtHead(val);
            return;
        }

        Node temp = head;
        int count = 0;

        while (temp != null && count < index - 1) {
            temp = temp.next;
            count++;
        }

        if (temp == null) return;

        Node node = new Node(val);
        node.next = temp.next;
        temp.next = node;
    }

    public void deleteAtIndex(int index) {

        if (head == null) return;

        if (index == 0) {
            head = head.next;
            return;
        }

        Node temp = head;
        int count = 0;

        while (temp.next != null && count < index - 1) {
            temp = temp.next;
            count++;
        }

        if (temp.next != null) {
            temp.next = temp.next.next;
        }
    }
}