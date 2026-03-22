package main

import (
	"fmt"
	"log"
	"os"
	"os/exec"
	"path/filepath"
)

func main() {
	if err := initializeConfig(); err != nil {
		log.Printf("Warning: configuration initialization failed: %v", err)
	}

	if needsInstall() {
		fmt.Println("Playwright browsers missing. Installing...")
		if err := installDependencies(); err != nil {
			log.Fatalf("Critical error during dependency installation: %v", err)
		}
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
	// Check Playwright using environment variable or default path
	path := os.Getenv("PLAYWRIGHT_BROWSERS_PATH")
	if path == "" {
		path = "/bot/playwright-browsers"
	}
	if _, err := os.Stat(filepath.Join(path, "chromium")); os.IsNotExist(err) {
		return true
	}
	return false
}

func installDependencies() error {
	path := os.Getenv("PLAYWRIGHT_BROWSERS_PATH")
	if path != "" {
		fmt.Printf("Ensuring directory exists: %s\n", path)
		if err := os.MkdirAll(path, 0755); err != nil {
			return fmt.Errorf("failed to create playwright browsers directory: %w", err)
		}
	}

	steps := [][]string{
		{"python", "-m", "playwright", "install", "chromium"},
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
	exec.Command("apt-get", "clean").Run()
	os.RemoveAll("/var/lib/apt/lists/")

	return nil
}

func runBot() error {
	cmd := exec.Command("python", "/bot/main.py")
	cmd.Stdout = os.Stdout
	cmd.Stderr = os.Stderr
	cmd.Stdin = os.Stdin
	return cmd.Run()
}
