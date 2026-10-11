output "certificate_arn" {
  description = "The ARN of the validated ACM certificate."
  value       = aws_acm_certificate_validation.this.certificate_arn
}

output "certificate_domain" {
  description = "The primary domain name of the certificate."
  value       = aws_acm_certificate.this.domain_name
}

output "zone_id" {
  description = "The Route 53 hosted zone ID."
  value       = data.aws_route53_zone.this.zone_id
}

