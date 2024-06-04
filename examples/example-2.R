library(geoarrow)
library(ggplot2)
nc <- sf::read_sf(system.file("shape/nc.shp", package = "sf"))
write_geoparquet(nc, "nc.parquet")
nc_pq<-read_geoparquet("nc.parquet")

nc_pq %>%
  geoarrow_collect_sf()%>%
  ggplot() +
  geom_sf()
