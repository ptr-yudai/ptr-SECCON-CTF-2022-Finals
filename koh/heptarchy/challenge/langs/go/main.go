package main
import "fmt"

var counter int = 0

func shrinker(c chan int, quit chan int) {
	for {
		n := <- c
		if n == 1 {
			quit <- 0
			break
		} else if n % 2 == 0 {
			counter += 1
			c <- n / 2
		} else {
			c <- n
		}
	}
}

func expander(c chan int, quit chan int) {
	for {
		n := <- c
		if n == 1 {
			quit <- 0
			break
		} else if n % 2 == 0 {
			c <- n
		} else {
			counter += 1
			c <- n * 3 + 1
		}
	}
}

func main() {
	var n int
	fmt.Print("Number: ")
	fmt.Scan(&n)
	if n <= 0 {
		fmt.Println("Invalid number")
		return
	}

	fmt.Println("[DEBUG] quit := make(chan int)")
	quit := make(chan int)
	fmt.Println("[DEBUG] c := make(chan int)")
	c := make(chan int)
	fmt.Println("[DEBUG] go shrinker(c, quit)")
	go shrinker(c, quit)
	fmt.Println("[DEBUG] go expander(c, quit)")
	go expander(c, quit)
	c <- n
	<-quit

	fmt.Println(counter)
}
