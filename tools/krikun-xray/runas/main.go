// SPDX-License-Identifier: GPL-3.0-or-later
// На ГУ systemd не стартует User= для uid без записи в passwd (см. jap-wireproxy/runas).
package main

import (
	"fmt"
	"os"
	"strconv"
	"syscall"
)

func main() {
	if len(os.Args) < 3 {
		fmt.Fprintln(os.Stderr, "usage: krikun-runas UID PROGRAM [ARGS...]")
		os.Exit(2)
	}
	uid, err := strconv.Atoi(os.Args[1])
	if err != nil || uid <= 0 || uid > 65533 {
		fmt.Fprintln(os.Stderr, "krikun-runas: UID must be 1..65533")
		os.Exit(2)
	}
	if err := syscall.Setgroups(nil); err != nil {
		fail("setgroups", err)
	}
	if err := syscall.Setgid(uid); err != nil {
		fail("setgid", err)
	}
	if err := syscall.Setuid(uid); err != nil {
		fail("setuid", err)
	}
	if syscall.Getuid() != uid || syscall.Geteuid() != uid || syscall.Getgid() != uid || syscall.Setuid(0) == nil {
		fmt.Fprintln(os.Stderr, "krikun-runas: root was not dropped")
		os.Exit(1)
	}
	fail("exec "+os.Args[2], syscall.Exec(os.Args[2], os.Args[2:], os.Environ()))
}

func fail(what string, err error) {
	fmt.Fprintf(os.Stderr, "krikun-runas: %s: %v\n", what, err)
	os.Exit(1)
}