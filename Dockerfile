FROM nginx:alpine

RUN mkdir -p /usr/share/nginx/html/assets

COPY index.html /usr/share/nginx/html/index.html
COPY styles.css /usr/share/nginx/html/styles.css
COPY assets/library-view-hero.jpg /usr/share/nginx/html/assets/library-view-hero.jpg
COPY assets/library-complete.jpg /usr/share/nginx/html/assets/library-complete.jpg
COPY assets/bookshelf-view.jpg /usr/share/nginx/html/assets/bookshelf-view.jpg
COPY assets/note-view.jpg /usr/share/nginx/html/assets/note-view.jpg

EXPOSE 80
