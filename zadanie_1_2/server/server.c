#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdint.h>

#include <unistd.h>
#include <arpa/inet.h>
#include <sys/socket.h>
#include <netinet/in.h>

#include <openssl/sha.h>

#define DEFAULT_PORT    9000
#define FILE_SIZE       10000
#define CHUNK_SIZE      100
#define MAX_DGRAM_SIZE  2048

#define MSG_START 'S'
#define MSG_DATA  'D'
#define MSG_ACK   'A'
#define MSG_HASH  'H'

typedef struct {
    int initialized;
    uint8_t buffer[FILE_SIZE];
    uint32_t file_size;
    uint16_t chunk_size;
    uint32_t expected_seq;
    uint32_t received_bytes;
} FileContext;

static void init_context(FileContext *ctx) {
    memset(ctx, 0, sizeof(*ctx));
    ctx->initialized = 0;
}

static void send_ack(int sockfd,
         struct sockaddr_in *cliaddr,
         socklen_t cli_len,
         uint32_t seq) {

    
    uint8_t buf[1 + 4];
    uint32_t seq_net;

    buf[0] = (uint8_t)MSG_ACK;
    seq_net = htonl(seq);
    memcpy(buf + 1, &seq_net, sizeof(seq_net));

    if (sendto(sockfd, buf, sizeof(buf), 0,
               (struct sockaddr *)cliaddr, cli_len) < 0) {
        perror("sendto (ACK)");
    }
}

static void send_hash(int sockfd,
          struct sockaddr_in *cliaddr,
          socklen_t cli_len,
          const uint8_t *data,
          uint32_t len) {
    uint8_t hash[SHA256_DIGEST_LENGTH];
    uint8_t buf[1 + SHA256_DIGEST_LENGTH];
    int i;

    SHA256(data, len, hash);

    buf[0] = (uint8_t)MSG_HASH;
    memcpy(buf + 1, hash, SHA256_DIGEST_LENGTH);

    if (sendto(sockfd, buf, sizeof(buf), 0,
               (struct sockaddr *)cliaddr, cli_len) < 0) {
        perror("sendto (hash)");
    }

    printf("Server hash: ");
    for (i = 0; i < SHA256_DIGEST_LENGTH; i++) {
        printf("%02x", hash[i]);
    }
    printf("\n");
}


static void
handle_start(FileContext *ctx, const uint8_t *buf, ssize_t len)
{
    uint32_t file_size_net;
    uint16_t chunk_size_net;
    uint32_t file_size_host;
    
    if (len < 1 + 4 + 2) {
        fprintf(stderr, "START: pakiet za krótki\n");
        return;
    }
    
    uint16_t chunk_size_host;

    memcpy(&file_size_net, buf + 1, 4);
    memcpy(&chunk_size_net, buf + 5, 2);

    file_size_host = ntohl(file_size_net);
    chunk_size_host = ntohs(chunk_size_net);

    printf("Odebrano START: file_size=%u chunk_size=%u\n",
           file_size_host, chunk_size_host);

    if (file_size_host != FILE_SIZE) {
        fprintf(stderr,
                "START: oczekiwano file_size=%d, a dostano %u - ignoruję START\n",
                FILE_SIZE, file_size_host);
        return;
    }
    if (chunk_size_host != CHUNK_SIZE) {
        fprintf(stderr,
                "START: oczekiwano chunk_size=%d, a dostano %u - ignoruję START\n",
                CHUNK_SIZE, chunk_size_host);
        return;
    }

    memset(ctx->buffer, 0, sizeof(ctx->buffer));
    ctx->file_size = file_size_host;
    ctx->chunk_size = chunk_size_host;

    ctx->expected_seq = 0;
    ctx->received_bytes = 0;
    ctx->initialized = 1;

    printf("Kontekst zainicjalizowany, oczekuje na dane...\n");
}


static void
handle_data(FileContext *ctx, const uint8_t *buf, ssize_t len)
{
    uint32_t seq_net;
    uint16_t data_len_net;
    uint32_t seq;
    uint16_t data_len;
    uint32_t offset;

    if (!ctx->initialized) {
        fprintf(stderr, "DATA: brak START\n");
        return;
    }

    if (len < 1 + 4 + 2) {
        fprintf(stderr, "DATA: pakiet za krótki\n");
        return;
    }

    memcpy(&seq_net, buf + 1, 4);
    memcpy(&data_len_net, buf + 5, 2);

    seq = ntohl(seq_net);
    data_len = ntohs(data_len_net);

    if ((size_t)(1 + 4 + 2 + data_len) > (size_t)len) {
        fprintf(stderr, "DATA: niezgodnosc długosci data_len\n");
        return;
    }

    if (seq == ctx->expected_seq) {
        offset = seq * ctx->chunk_size;

        if (offset + data_len > ctx->file_size) {
            fprintf(stderr, "DATA: pakiet wykracza poza rozmiar pliku\n");
            return;
        }

        memcpy(ctx->buffer + offset, buf + 7, data_len);
        ctx->received_bytes += data_len;
        ctx->expected_seq++;

        printf("DATA: seq=%u, data_len=%u, received_bytes=%u\n",
               seq, data_len, ctx->received_bytes);
    } else if (seq < ctx->expected_seq) {
        printf("DATA: dublikat seq=%u (expected=%u)\n",
               seq, ctx->expected_seq);
    } else {
        fprintf(stderr, "DATA: nieoczekiwany seq=%u (expected=%u)\n",
                seq, ctx->expected_seq);
    }
}

int
main(int argc, char **argv)
{
    setvbuf(stdout, NULL, _IONBF, 0);
    int port;
    int sockfd;
    struct sockaddr_in servaddr;
    FileContext ctx;

    if (argc >= 2) {
        port = atoi(argv[1]);
    } else {
        port = DEFAULT_PORT;
    }

    sockfd = socket(AF_INET, SOCK_DGRAM, 0);
    if (sockfd < 0) {
        perror("socket");
        return 1;
    }

    memset(&servaddr, 0, sizeof(servaddr));
    servaddr.sin_family = AF_INET;
    servaddr.sin_addr.s_addr = htonl(INADDR_ANY);

    servaddr.sin_port = htons((uint16_t)port);

    if (bind(sockfd, (struct sockaddr *)&servaddr, sizeof(servaddr)) < 0) {
        perror("bind");
        close(sockfd);
        return 1;
    }

    printf("Serwer nasłuchuje na porcie UDP %d\n", port);

    init_context(&ctx);

    for (;;) {
        uint8_t buf[MAX_DGRAM_SIZE];
        struct sockaddr_in cliaddr;
        socklen_t cli_len;
        ssize_t n;
        uint8_t type;

        cli_len = sizeof(cliaddr);
        n = recvfrom(sockfd, buf, sizeof(buf), 0,
                     (struct sockaddr *)&cliaddr, &cli_len);
        if (n < 0) {
            perror("recvfrom");
            continue;
        }
        if (n == 0) {
            continue;
        }

        type = buf[0];

        if (type == (uint8_t)MSG_START) {
            handle_start(&ctx, buf, n);
            send_ack(sockfd, &cliaddr, cli_len, 0);
        } else if (type == (uint8_t)MSG_DATA) {
            uint32_t seq_net, seq_host;

            if (n < 1 + 4) {
                fprintf(stderr, "DATA: pakiet za krótki do odczytu seq\n");
                continue;
            }

            memcpy(&seq_net, buf + 1, 4);
            seq_host = ntohl(seq_net);

            handle_data(&ctx, buf, n);

            send_ack(sockfd, &cliaddr, cli_len, seq_host);

            if (ctx.initialized && ctx.received_bytes == ctx.file_size) {
                printf("Odebrano pełny plik %u bajtow\n", ctx.file_size);
                send_hash(sockfd, &cliaddr, cli_len,
                          ctx.buffer, ctx.file_size);

                init_context(&ctx);
            }
        } else {
            fprintf(stderr, "Nieznany typ pakietu: %c\n", type);
        }
    }

    close(sockfd);
    return 0;
}
