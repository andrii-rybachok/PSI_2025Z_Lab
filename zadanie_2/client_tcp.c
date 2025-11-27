#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <sys/types.h>
#include <sys/socket.h>
#include <arpa/inet.h>
#include <netinet/in.h>

#define HOST "127.0.0.1"
#define BUF 256

void cut_n(char *s) {
    size_t len = strlen(s);
    if (len > 0 && s[len - 1] == '\n') s[len - 1] = '\0';
}

int main(int argc, char **argv) {
    int sockfd;
    struct sockaddr_in addr;
    char num1[BUF];
    char op[BUF];
    // 

    char num2[BUF];
    char send_buf[BUF];
    char recv_buf[BUF];
    int port;

    if (argc < 2) {
        port = 8000;
        printf("brak portu, uzywam %d\n", port);
    } else {
        port = atoi(argv[1]);
    }

    sockfd = socket(AF_INET, SOCK_STREAM, 0);

    if (sockfd < 0) {
        perror("socket");
        return 1;
    }

    memset(&addr, 0, sizeof(addr));
    addr.sin_family = AF_INET;



    addr.sin_port = htons(port);

    if (inet_pton(AF_INET, HOST, &addr.sin_addr) <= 0) {
        perror("inet_pton");
        close(sockfd);
        return 1;
    }

    if (connect(sockfd, (struct sockaddr *)&addr,sizeof(addr)) < 0) {
        perror("connect");
        close(sockfd);
        return 1;
    }

    printf("polaczono %s:%d\n", HOST, port);

    printf("a: ");

    if (fgets(num1, sizeof(num1), stdin) == NULL) {
        fprintf(stderr, "blad wejscia\n");
        close(sockfd);
        return 1;
    }

    printf("op: ");
    if (fgets(op, sizeof(op), stdin) == NULL) {
        fprintf(stderr, "blad wejscia\n");
        close(sockfd);
        return 1;
    }

    printf("b: ");
    if (fgets(num2, sizeof(num2), stdin) == NULL) {
        fprintf(stderr, "blad wejscia\n");
        close(sockfd);
        return 1;
    }

    cut_n(num1);
    cut_n(op);
    cut_n(num2);

    snprintf(send_buf, sizeof(send_buf), "%s\n", num1);
    if (send(sockfd, send_buf, strlen(send_buf), 0) < 0) {
        perror("send num1");
        close(sockfd);
        return 1;
    }

    snprintf(send_buf, sizeof(send_buf), "%s\n", op);
    if (send(sockfd, send_buf, strlen(send_buf), 0) < 0) {
        perror("send op");
        close(sockfd);
        return 1;
    }

    snprintf(send_buf, sizeof(send_buf), "%s\n", num2);
    if (send(sockfd, send_buf, strlen(send_buf), 0) < 0) {
        perror("send num2");
        
        close(sockfd);
        return 1;
    }

    ssize_t n;
    size_t total = 0;

    while ((n = recv(sockfd,
                     recv_buf + total,
                     sizeof(recv_buf) - 1 - total,
                     0)) > 0) {
        total += (size_t)n;
        if (total >= sizeof(recv_buf) - 1) break;
        if (recv_buf[total - 1] == '\n') break;
    }

    if (n < 0) {
        perror("recv");

        close(sockfd);
        return 1;
    }

    recv_buf[total] = '\0';
    cut_n(recv_buf);

    printf("wynik: %s\n", recv_buf);
    printf("expr: %s %s %s = %s\n", num1, op, num2, recv_buf);

    close(sockfd);
    return 0;
}
