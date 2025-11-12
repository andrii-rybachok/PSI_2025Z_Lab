#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <arpa/inet.h>
#include <unistd.h>
#include <sys/time.h>
#include <netdb.h>

#define MAX_SIZE 65507
#define SIXTEEN_BIT_SIZE 65536

int main(int argc, char *argv[]) {
    if (argc < 3) {
        printf("Użycie: %s <nazwa_serwera> <port>\n", argv[0]);
        exit(1);
    }

    int sockfd = socket(AF_INET, SOCK_DGRAM, 0);
    if (sockfd < 0) {
        perror("socket");
        return 1;
    }

    struct hostent *hp;
    hp = gethostbyname(argv[1]);
    if (hp == NULL) {
        fprintf(stderr, "%s: unknown host\n", argv[1]);
        exit(2);
    }

    struct sockaddr_in server_addr;
    memset(&server_addr, 0, sizeof(server_addr));
    server_addr.sin_family = AF_INET;
    memcpy(&server_addr.sin_addr, hp->h_addr, hp->h_length);
    server_addr.sin_port = htons(atoi(argv[2]));

    char buffer[MAX_SIZE];
    char recv_buf[1024];
    size_t power = 2;
    size_t size = power - 1;
    printf("Testowanie rozmiarów datagramów...\n");

    while (power <= SIXTEEN_BIT_SIZE) {
        memset(buffer, 'x', size);

        struct timeval start, end;
        gettimeofday(&start, NULL);

        ssize_t sent = sendto(sockfd, buffer, size, 0,
                              (struct sockaddr *)&server_addr, sizeof(server_addr));
        if (sent < 0) {
            perror("sendto");
            break;
        }

        socklen_t addr_len = sizeof(server_addr);
        ssize_t recv_len = recvfrom(sockfd, recv_buf, sizeof(recv_buf), 0,
                                    (struct sockaddr *)&server_addr, &addr_len);
        gettimeofday(&end, NULL);

        if (recv_len > 0) {
            double rtt = (end.tv_sec - start.tv_sec) * 1000.0
                         + (end.tv_usec - start.tv_usec) / 1000.0;
            printf("%zu bajtów OK, RTT = %.3f ms\n", size, rtt);
            power *= 2;
            size = power - 1 > MAX_SIZE ? MAX_SIZE : power - 1;
        } else {
            printf("Brak odpowiedzi dla rozmiaru %zu bajtów\n", size);
            break;
        }
    }

    close(sockfd);
    return 0;
}
