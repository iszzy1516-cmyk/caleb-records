output "server_public_ip" {
  description = "Public IP address of the EC2 instance"
  value       = aws_eip.app.public_ip
}

output "server_private_ip" {
  description = "Private IP address of the EC2 instance"
  value       = aws_instance.app.private_ip
}

output "server_id" {
  description = "EC2 instance ID"
  value       = aws_instance.app.id
}

output "ssh_command" {
  description = "Command to SSH into the server"
  value       = "ssh -i ~/.ssh/${var.key_name}.pem ubuntu@${aws_eip.app.public_ip}"
}

output "s3_backup_bucket" {
  description = "S3 bucket for backups and uploads"
  value       = aws_s3_bucket.backups.bucket
}

output "rds_endpoint" {
  description = "RDS PostgreSQL endpoint (if created)"
  value       = var.create_rds ? aws_db_instance.postgres[0].endpoint : null
}

output "ansible_inventory_path" {
  description = "Path to the generated Ansible inventory file"
  value       = local_file.ansible_inventory.filename
}

output "ansible_group_vars_example_path" {
  description = "Path to the generated Ansible group_vars example file"
  value       = local_file.ansible_group_vars_example.filename
}
