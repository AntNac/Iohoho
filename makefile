CC = gcc
CFLAGS = -Wall -lm -lpthread
TARGET = server
SRC = socket-server.c

all: $(TARGET)

$(TARGET): $(SRC)
	$(CC) $(SRC) -o $(TARGET) $(CFLAGS)

clean:
	rm -f $(TARGET)
