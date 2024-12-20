package main

import (
    "bufio"
    "fmt"
    "log"
    "net"
    "os"
    "strings"
)

func main() {
    // Connect to the IRC server
    conn, err := net.Dial("tcp", "irc.libera.chat:6667")
    if err != nil {
        log.Fatal(err)
    }
    defer conn.Close()

    // Set up a reader for user input
    reader := bufio.NewReader(os.Stdin)

    // Basic IRC handshake
    fmt.Fprintf(conn, "USER gobot 0 * :Gobot IRC Client\r\n")
    fmt.Fprintf(conn, "NICK gobot\r\n")

    // Join a channel
    fmt.Fprintf(conn, "JOIN #test\r\n")

    // Start a goroutine to read from the server
    go func() {
        for {
            message, err := bufio.NewReader(conn).ReadString('\n')
            if err != nil {
                log.Println(err)
                return
            }
            fmt.Print(message)
        }
    }()

    // Main loop to handle user input
    for {
        // Read user input
        input, _ := reader.ReadString('\n')
        input = strings.TrimSpace(input)

        // Send message to the server
        if input != "" {
            fmt.Fprintf(conn, "PRIVMSG #test :%s\r\n", input)
        }
    }
}
