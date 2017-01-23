FROM fliem/lhab_docker:v0.8.8.dev.nolhpipe

# recent changes
#### DCM2NIIX
WORKDIR /root
RUN apt-get update && apt-get upgrade -y && \
    apt-get install -y build-essential pkg-config libyaml-cpp-dev libyaml-cpp0.5 cmake libboost-dev git pigz unzip && \
	  apt-get clean -y && apt-get autoclean -y && apt-get autoremove -y
RUN cd /tmp && \
    wget https://github.com/rordenlab/dcm2niix/archive/672f4d2951fe752316aefa90708123af9e401eb1.zip -O dcm2niix.zip && unzip dcm2niix.zip \
  	cd dcm2niix* && mkdir build && cd build && \
  	cmake -DBATCH_VERSION=ON .. && \
  	make && make install

COPY lhab_pipelines /code/lhab_pipelines/
COPY scripts /code/lhab_pipelines/
COPY version /version

CMD ["/bin/bash"]
