/* SPDX-License-Identifier: GPL-3.0-or-later */
/* UID PROGRAM ARGS — syscall setuid, как jap-runas (mgu-apps). */
#define _GNU_SOURCE
#include <errno.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>

static void die(const char *w) {
	perror(w);
	exit(1);
}

int main(int argc, char **argv) {
	if (argc < 3) {
		fprintf(stderr, "usage: krikun-runas UID PROGRAM [ARGS...]\n");
		return 2;
	}
	char *e = NULL;
	long uid_l = strtol(argv[1], &e, 10);
	if (e == argv[1] || *e || uid_l <= 0 || uid_l > 65533)
		die("uid");
	uid_t uid = (uid_t)uid_l;

	if (setgroups(0, NULL))
		die("setgroups");
	if (setgid(uid))
		die("setgid");
	if (setuid(uid))
		die("setuid");
	if (getuid() != uid || geteuid() != uid || getgid() != uid)
		die("drop");
	if (setuid(0) == 0) {
		fprintf(stderr, "krikun-runas: root was not dropped\n");
		return 1;
	}
	execv(argv[2], &argv[2]);
	die(argv[2]);
	return 1;
}