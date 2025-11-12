#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <arpa/inet.h>
#include <unistd.h>

#define BUFFER_SIZE 65507

int main() {
    setvbuf(stdout, NULL, _IONBF, 0);
    int sockfd;
    struct sockaddr_in server_addr, client_addr;
    socklen_t addr_len = sizeof(client_addr);
    char buffer[BUFFER_SIZE];
    const char *reply = "ACK"; 

    if ((sockfd = socket(AF_INET, SOCK_DGRAM, 0)) < 0) {
        perror("socket error");
        exit(EXIT_FAILURE);
    }

    memset(&server_addr, 0, sizeof(server_addr));
    server_addr.sin_family = AF_INET;
    server_addr.sin_addr.s_addr = INADDR_ANY;
    server_addr.sin_port = htons(12345);

    if (bind(sockfd, (struct sockaddr *)&server_addr, addr_len) < 0) {
        perror("bind error");
        close(sockfd);
        exit(EXIT_FAILURE);
    }

    if (getsockname(sockfd,(struct sockaddr *) &server_addr,&addr_len) == -1) {
        perror("getting socket name");
        exit(2);
    }

    printf("Serwer UDP uruchomiony na porcie %d\n", ntohs(server_addr.sin_port));
    printf("Adres IP serwera: %s\n", inet_ntoa(server_addr.sin_addr));

    while (1) {
        ssize_t recv_len = recvfrom(sockfd, buffer, BUFFER_SIZE, 0,
                                   (struct sockaddr *)&client_addr, &addr_len);
        if (recv_len < 0) {
            perror("recvfrom error");
            continue;
        }

        printf("Odebrano datagram o długości %ld bajtów\n", recv_len);

        sendto(sockfd, reply, strlen(reply), 0,
               (struct sockaddr *)&client_addr, addr_len);
    }

    close(sockfd);
    return 0;
}
