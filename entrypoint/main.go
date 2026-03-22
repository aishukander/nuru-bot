package main

import (
	"bufio"
	"bytes"
	"fmt"
	"log"
	"os"
	"os/exec"
	"path/filepath"
	"strings"
)

func main() {
	if err := initializeConfig(); err != nil {
		log.Printf("Warning: configuration initialization failed: %v", err)
	}

	if needsInstall() {
		fmt.Println("Requirement check failed. Installing/Repairing dependencies...")
		if err := installDependencies(); err != nil {
			log.Fatalf("Critical error during dependency installation: %v", err)
		}
		fmt.Println("Dependencies synchronized.")
	}

	fmt.Println("Starting bot...")
	if err := runBot(); err != nil {
		log.Fatalf("Bot crashed: %v", err)
	}
}

func initializeConfig() error {
	src := "/tmp/toml"
	dst := "/bot/toml/"

	if _, err := os.Stat(src); os.IsNotExist(err) {
		return nil
	}

	entries, err := os.ReadDir(dst)
	if err == nil && len(entries) == 0 {
		fmt.Printf("Initializing config files from %s to %s\n", src, dst)
		err := filepath.Walk(src, func(path string, info os.FileInfo, err error) error {
			if err != nil {
				return err
			}
			if info.IsDir() {
				return nil
			}
			relPath, _ := filepath.Rel(src, path)
			targetPath := filepath.Join(dst, relPath)

			if err := os.MkdirAll(filepath.Dir(targetPath), 0755); err != nil {
				return err
			}

			data, err := os.ReadFile(path)
			if err != nil {
				return err
			}
			return os.WriteFile(targetPath, data, info.Mode())
		})
		if err != nil {
			return err
		}
	}

	os.RemoveAll(src)
	return nil
}

func needsInstall() bool {
	// Check libopus0
	cmd := exec.Command("ldconfig", "-p")
	output, _ := cmd.Output()
	if !bytes.Contains(output, []byte("libopus.so.0")) {
		fmt.Println("libopus0 missing.")
		return true
	}

	// Check Playwright
	if _, err := os.Stat("/root/.cache/ms-playwright/chromium"); os.IsNotExist(err) {
		fmt.Println("Playwright browsers missing.")
		return true
	}

	// Check Pip dependencies
	if _, err := os.Stat("/bot/requirements.txt"); err == nil {
		installed, err := exec.Command("pip", "list", "--format=freeze").Output()
		if err != nil {
			fmt.Printf("Warning: could not list pip packages: %v\n", err)
			return true
		}

		installedPkgs := make(map[string]bool)
		scanner := bufio.NewScanner(bytes.NewReader(installed))
		for scanner.Scan() {
			pkg := strings.Split(scanner.Text(), "==")[0]
			installedPkgs[strings.ToLower(pkg)] = true
		}

		file, err := os.Open("/bot/requirements.txt")
		defer file.Close()
		if err != nil {
			return true
		}

		scanner = bufio.NewScanner(file)
		for scanner.Scan() {
			line := strings.TrimSpace(scanner.Text())
			if line == "" || strings.HasPrefix(line, "#") {
				continue
			}
			// Simplified package name parsing (removes versions and comments)
			parts := strings.FieldsFunc(line, func(r rune) bool {
				return r == '=' || r == '>' || r == '<' || r == '#'
			})
			if len(parts) > 0 {
				reqPkg := strings.ToLower(strings.TrimSpace(parts[0]))
				if !installedPkgs[reqPkg] {
					fmt.Printf("Missing dependency: %s\n", reqPkg)
					return true
				}
			}
		}
	}

	return false
}

func installDependencies() error {
	steps := [][]string{
		{"apt-get", "update"},
		{"apt-get", "install", "-y", "--no-install-recommends", "libopus0"},
		{"pip", "install", "--no-cache-dir", "--upgrade", "pip"},
		{"pip", "install", "--no-cache-dir", "-r", "/bot/requirements.txt"},
		{"python", "-m", "playwright", "install", "--with-deps", "chromium"},
	}

	for _, args := range steps {
		fmt.Printf("Executing: %v\n", args)
		cmd := exec.Command(args[0], args[1:]...)
		cmd.Stdout = os.Stdout
		cmd.Stderr = os.Stderr
		if err := cmd.Run(); err != nil {
			return fmt.Errorf("command %v failed: %w", args, err)
		}
	}

	// Cleanup
	fmt.Println("Cleaning up...")
	exec.Command("apt-get", "purge", "-y", "--auto-remove").Run()
	exec.Command("apt-get", "clean").Run()
	os.RemoveAll("/var/lib/apt/lists/")
	os.RemoveAll("/root/.cache/pip/")

	return nil
}

func runBot() error {
	cmd := exec.Command("python", "/bot/main.py")
	cmd.Stdout = os.Stdout
	cmd.Stderr = os.Stderr
	cmd.Stdin = os.Stdin
	return cmd.Run()
}
