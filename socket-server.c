#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <pthread.h>
#include <sys/socket.h>
#include <netinet/in.h>
#include <arpa/inet.h>
#include <time.h>
#include <math.h>

#define MAX_PLAYERS 2
#define MAX_BOXES 100
#define MAX_BULLETS 500
#define WIDTH 1920
#define HEIGHT 1080

typedef struct {
    int id;
    float x, y;
    int level;
    int color[3];
    double hp;
    double max_hp;
    int velocity;
	int size;
	int damage;
    time_t last_shot_time;
} Player;

typedef struct {
    int id;
    float x, y;
    float endx, endy;
    float velocity_x, velocity_y;
    int active;
    int player_id;
} Bullet;

typedef struct {
    int id;
    float x, y;
    int hp;
    int size;
} Box;

Player players[MAX_PLAYERS];
Box boxes[MAX_BOXES];
Bullet bullets[MAX_BULLETS];
int num_players = 0;
int num_boxes = 10;
int num_bullets = 0;
pthread_mutex_t mutex = PTHREAD_MUTEX_INITIALIZER;

void initialize_game() {
    srand(time(NULL));
    
    for (int i = 0; i < num_boxes; i++) {
        boxes[i].id = i;
        boxes[i].x = rand() % WIDTH;
        boxes[i].y = rand() % HEIGHT;
        boxes[i].hp = 20;
        boxes[i].size = 15;
    }
    
    for (int i = 0; i < MAX_PLAYERS; i++) {
        players[i].id = i;
        players[i].x = rand() % WIDTH;
        players[i].y = rand() % HEIGHT;
        players[i].level = 1;
        players[i].color[0] = rand() % 256;
        players[i].color[1] = rand() % 256;
        players[i].color[2] = rand() % 256;
        players[i].hp = 100.0;
        players[i].max_hp = 100.0;
        players[i].velocity = 5;
		players[i].size = 15;
		players[i].damage = 5;
        players[i].last_shot_time = 0;
    }
}

void remove_inactive_bullets() {
    int j = 0;
    for (int i = 0; i < num_bullets; i++) {
        if (bullets[i].active) {
            if (i != j) {
                bullets[j] = bullets[i];
                bullets[j].id = j;
            }
            j++;
        }
    }
    num_bullets = j;
}

void update_boxes() {
    int j = 0;
    for (int i = 0; i < num_boxes; i++) {
        if (boxes[i].hp<=0) {
            boxes[i].x = rand() % WIDTH;
			boxes[i].y = rand() % HEIGHT;
			boxes[i].hp = 20;
        }
    }
}

void level_up(Player* player){
    player->level++;
    player->size += 1;
    if(player->level % 5 == 0 && player->velocity > 1){
        player->velocity--;
    }
	player->damage++;
	player->max_hp+=10;
}

void heal(){
	for(int i=0;i<num_players;i++){
		if(players[i].hp<players[i].max_hp){
			players[i].hp+=0.01;
		}
	}
}

void update_bullets() {
    for (int i = 0; i < num_bullets; i++) {
        if (!bullets[i].active) continue;
        
        bullets[i].x += bullets[i].velocity_x;
        bullets[i].y += bullets[i].velocity_y;
        
        float dx = bullets[i].endx - bullets[i].x;
        float dy = bullets[i].endy - bullets[i].y;
        float distance = sqrt(dx*dx + dy*dy);
        
        if (distance < 5) {
            bullets[i].active = 0;
        }

		for(int j=0;j<num_players;j++){
			float dist = sqrt(pow(bullets[i].x - players[j].x, 2) +
                              pow(bullets[i].y - players[j].y, 2));

			if(dist < players[j].size + players[j].level * 3 && bullets[i].player_id != players[j].id){
				players[j].hp -= players[bullets[i].player_id].damage;
				bullets[i].active = 0;
			}
		}
        
        for (int j = 0; j < num_boxes; j++) {
            if (boxes[j].hp <= 0) continue;
            
            float dist = sqrt(pow(bullets[i].x - boxes[j].x, 2) +
                              pow(bullets[i].y - boxes[j].y, 2));
            
            if (dist <= boxes[j].size) {
                bullets[i].active = 0;
                boxes[j].hp -= players[bullets[i].player_id].damage;
                
                if (boxes[j].hp <= 0) {
                    level_up(&players[bullets[i].player_id]);
                }
                
                break;
            }
        }
    }
}

void *client_handler(void *socket_desc) {
    int sock = *(int*)socket_desc;
    int player_id = -1;
    
    pthread_mutex_lock(&mutex);
    if (num_players < MAX_PLAYERS) {
        player_id = num_players++;
    }
    pthread_mutex_unlock(&mutex);
    
    if (player_id == -1) {
        close(sock);
        return NULL;
    }
    
    char id_msg[2];
    snprintf(id_msg, sizeof(id_msg), "%d", player_id);
    send(sock, id_msg, strlen(id_msg), 0);
    
    char buffer[1024];
    while (1) {
        int n = recv(sock, buffer, sizeof(buffer), 0);
        if (n <= 0) break;
        buffer[n] = '\0';
        
        int right = 0, left = 0, up = 0, down = 0, shoot = 0;
        float mouse_x = 0, mouse_y = 0;
        
        sscanf(buffer, "%d,%d,%d,%d,%d,%f,%f", 
               &right, &left, &up, &down, &shoot, &mouse_x, &mouse_y);
        
        pthread_mutex_lock(&mutex);
        
        if (right) players[player_id].x += players[player_id].velocity;
        if (left) players[player_id].x -= players[player_id].velocity;
        if (up) players[player_id].y -= players[player_id].velocity;
        if (down) players[player_id].y += players[player_id].velocity;
        
        if (players[player_id].x < 0) players[player_id].x = 0;
        if (players[player_id].y < 0) players[player_id].y = 0;
        if (players[player_id].x > WIDTH) players[player_id].x = WIDTH;
        if (players[player_id].y > HEIGHT) players[player_id].y = HEIGHT;
        
        time_t now = time(NULL);
        if (shoot && difftime(now, players[player_id].last_shot_time) >= 0.2) {
            if (num_bullets < MAX_BULLETS) {
                Bullet b;
                b.id = num_bullets;

				float dx = mouse_x - players[player_id].x;
                float dy = mouse_y - players[player_id].y;
                float distance = sqrt(dx*dx + dy*dy);
				double sin=(mouse_y-players[player_id].y)/distance;
                b.x = players[player_id].x+(players[player_id].size+(players[player_id].level*3))*sin;
                b.y = players[player_id].y+(players[player_id].size+(players[player_id].level*3))*sin;
                b.endx = mouse_x;
                b.endy = mouse_y;
                b.player_id = player_id;
                b.active = 1;
            
                
                if (distance > 0) {
                    b.velocity_x = dx / distance * 5;
                    b.velocity_y = dy / distance * 5;
                } else {
                    b.velocity_x = 0;
                    b.velocity_y = 0;
                }
                
                bullets[num_bullets++] = b;
                players[player_id].last_shot_time = now;
            }
        }
        
        update_bullets();
		remove_inactive_bullets();
		update_boxes();
		heal();
        
        char response[4096] = {0};
        char temp[256];
        
        for (int i = 0; i < MAX_PLAYERS; i++) {
		snprintf(temp, sizeof(temp), "%d,%.1f,%.1f,%d,%d,%d,%d,%.1f,%d,%.1f;", 
				players[i].id, players[i].x, players[i].y, players[i].level,
				players[i].color[0], players[i].color[1], players[i].color[2], 
				players[i].hp, players[i].size, players[i].max_hp);
		strcat(response, temp);
}
        strcat(response, "|");
        
        for (int i = 0; i < num_boxes; i++) {
            if (boxes[i].hp <= 0) continue;
            snprintf(temp, sizeof(temp), "%d,%.1f,%.1f,%d;", 
                    boxes[i].id, boxes[i].x, boxes[i].y, boxes[i].hp);
            strcat(response, temp);
        }
        strcat(response, "|");
        
        for (int i = 0; i < num_bullets; i++) {
            if (!bullets[i].active) continue;
            snprintf(temp, sizeof(temp), "%.1f,%.1f,%.1f,%.1f,%d;", 
                    bullets[i].x, bullets[i].y, 
                    bullets[i].endx, bullets[i].endy,
                    bullets[i].player_id);
            strcat(response, temp);
        }
        strcat(response, "|");
    
        
        
        send(sock, response, strlen(response), 0);
        pthread_mutex_unlock(&mutex);
    }
    
    pthread_mutex_lock(&mutex);
    num_players--;
    pthread_mutex_unlock(&mutex);
    
    close(sock);
    return NULL;
}

int main() {
    int server_fd, new_socket;
    struct sockaddr_in address;
    int opt = 1;
    int addrlen = sizeof(address);
    
    initialize_game();
    
    if ((server_fd = socket(AF_INET, SOCK_STREAM, 0)) == 0) {
        perror("socket failed");
        exit(EXIT_FAILURE);
    }
    
    if (setsockopt(server_fd, SOL_SOCKET, SO_REUSEADDR, &opt, sizeof(opt))) {
        perror("setsockopt");
        exit(EXIT_FAILURE);
    }
    
    address.sin_family = AF_INET;
    address.sin_addr.s_addr = INADDR_ANY;
    address.sin_port = htons(5000);
    
    if (bind(server_fd, (struct sockaddr *)&address, sizeof(address)) < 0) {
        perror("bind failed");
        exit(EXIT_FAILURE);
    }
    
    if (listen(server_fd, 3) < 0) {
        perror("listen");
        exit(EXIT_FAILURE);
    }
    
    printf("Game server started on port 5000\n");
    
    while (1) {
        if ((new_socket = accept(server_fd, (struct sockaddr *)&address, (socklen_t*)&addrlen)) < 0) {
            perror("accept");
            exit(EXIT_FAILURE);
        }
        
        printf("New connection from %s\n", inet_ntoa(address.sin_addr));
        
        pthread_t thread;
        int *new_sock = malloc(sizeof(int));
        *new_sock = new_socket;
        
        if (pthread_create(&thread, NULL, client_handler, (void*)new_sock) < 0) {
            perror("pthread_create");
            close(new_socket);
            free(new_sock);
        }
        
        pthread_detach(thread);
    }
    
    return 0;
}
