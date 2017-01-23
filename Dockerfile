FROM fliem/lhab_docker:v0.8.8.dev.nolhpipe

# recent changes
#### DCM2NIIX
WORKDIR /root
RUN apt-get update && apt-get upgrade -y && \
    apt-get install -y build-essential pkg-config libyaml-cpp-dev libyaml-cpp0.5 cmake libboost-dev git pigz && \
	  apt-get clean -y && apt-get autoclean -y && apt-get autoremove -y
RUN cd /tmp && \
  	git clone https://github.com/rordenlab/dcm2niix.git && \
  	cd dcm2niix && mkdir build && cd build && \
  	cmake -DBATCH_VERSION=ON .. && \
  	make && make install


COPY version /version

CMD ["/bin/bash"]
