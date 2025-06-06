import json
import math
import os

basic_config_path = "./config/config.json"

class Params():
    """
        A customized parameter parser.
    """
    def __init__(self, json_path):
        with open(json_path) as f:
            params = json.load(f)
            self.__dict__.update(params)

    def save(self, json_path):
        with open(json_path, 'w') as f:
            json.dump(self.__dict__, f, indent=4)

    def update(self, json_path):
        with open(json_path) as f:
            params = json.load(f)
            self.__dict__.update(params)

    @property
    def dict(self):
        return self.__dict__

class AutoConfig():
    """
        A Strong Config Manager, load a given config, do some changes, and save them.
    """
    def __init__(self, config):
        self.config = config

        self.G = config["G"]
        self.rho = config["rho"]
        self.sun_mass = config["sun_mass"]
        self.merging_threshold = config["merging_threshold"]
        self.per_step_time = config["per_step_time"]
        self.num_steps = config["num_steps"]
        self.basic_radii = config["basic_radii"]
        self.num_chunks = config["num_chunks"]
        
        init_config = config["init_config"]
        self.num_planets = init_config["num_planets"]
        self.pos_norm = init_config["pos_norm"]
        self.pos_bias = init_config["pos_bias"]
        self.v_norm = init_config["v_norm"]
        self.v_bias = init_config["v_bias"]

        figure_config = config["figure_config"]
        self.no_figure = figure_config["no_figure"]
        self.margin_bias = figure_config["margin_bias"]
        self.plot_scale = figure_config["plot_scale"]
        self.range_quantile = figure_config["range_quantile"]
        self.record_steps = figure_config["record_steps"]

        self.device = config["device"]
        
        self.metrics = self._get_metrics()

    def _reset(self, config): 
        self.__init__(config)

    def _get_metrics(self):
        # get the metrics from a given config
        metrics = {}
        metrics["merger_checking"] = self.pos_bias/(self.basic_radii*self.merging_threshold)
        metrics["orbit_constant"] = math.sqrt(self.G*self.sun_mass/self.pos_norm)/self.v_norm
        metrics["force_ratio"] = self.sun_mass * math.pow(self.pos_bias,2)/(self.rho * math.pow(self.basic_radii,3) * math.pow(self.pos_norm, 2))
        metrics["angular_velocity"] = self.per_step_time * self.v_norm/self.pos_norm
        metrics["init_pos_ratio"] = self.pos_bias/self.pos_norm
        metrics["init_vel_ratio"] = self.v_bias/self.v_norm
        metrics["line_density"] = self.basic_radii/self.pos_norm
        return metrics

    def _config_to_json(self, config, output_path):
        # save the config to a json file
        with open(output_path, 'w') as f: 
            f.write(json.dumps(config))

    def _reset_config(self, output_path):
        # generate a config and save
        config = {}
        config["G"] = self.G
        config["rho"] = self.rho
        config["sun_mass"] = self.sun_mass
        config["merging_threshold"] = self.merging_threshold
        config["per_step_time"] = self.per_step_time
        config["num_steps"] = self.num_steps
        config["basic_radii"] = self.basic_radii
        config["num_chunks"] = self.num_chunks
        
        init_config = {}
        init_config["num_planets"] = self.num_planets
        init_config["pos_norm"] = self.pos_norm
        init_config["pos_bias"] = self.pos_bias
        init_config["v_norm"] = self.v_norm
        init_config["v_bias"] = self.v_bias
        config["init_config"] = init_config
        
        figure_config = {}
        figure_config["no_figure"] = self.no_figure
        figure_config["margin_bias"] = self.margin_bias
        figure_config["plot_scale"] = self.plot_scale
        figure_config["range_quantile"] = self.range_quantile
        figure_config["record_steps"] = self.record_steps
        config["figure_config"] = figure_config

        config["device"] = self.device
        
        config["metrics"] = self.metrics
        
        self._config_to_json(config, output_path)
    
    def init_config_from_metrics(self, merger_checking, orbit_constant, force_ratio, angular_velocity, init_pos_ratio, init_vel_ratio, G, sun_mass, merging_threshold, pos_norm, output_path, **kwargs):
        # initialize a config from the metrics
        self.G = G
        self.sun_mass = sun_mass
        self.merging_threshold = merging_threshold
        self.pos_norm = pos_norm
        self.pos_bias = init_pos_ratio * pos_norm
        self.v_norm = math.sqrt(self.G*self.sun_mass/self.pos_norm)/orbit_constant
        self.v_bias = init_vel_ratio * self.v_norm
        self.per_step_time = angular_velocity * self.pos_norm/(self.v_norm)
        self.basic_radii = self.pos_bias/(self.merging_threshold * merger_checking)
        self.rho = self.sun_mass * math.pow(self.pos_bias,2)/(force_ratio * math.pow(self.basic_radii,3) * math.pow(self.pos_norm, 2))
        self.margin_bias = self.pos_norm
        self.metrics = self._get_metrics()
        output_path += f"-metrics-mode.json"
        self._reset_config(output_path)
        return output_path
        
    def identity_length(self, scale, output_path):
        # initialize a config from the identity transformation of length
        self.G = self.G/(math.pow(scale,3))
        self.rho = self.rho * math.pow(scale,3)
        self.basic_radii = self.basic_radii/scale
        self.pos_norm = self.pos_norm/scale
        self.pos_bias = self.pos_bias/scale
        self.v_norm = self.v_norm/scale
        self.v_bias = self.v_bias/scale
        self.margin_bias = self.margin_bias/scale
        self.metrics = self._get_metrics()
        output_path += f"-id-length-{scale}.json"
        self._reset_config(output_path)
        return output_path

    def identity_mass(self, scale, output_path):
        # initialize a config from the identity transformation of mass
        self.G = self.G * scale
        self.rho = self.rho/scale
        self.sun_mass = self.sun_mass/scale
        self.metrics = self._get_metrics()
        output_path += f"-id-mass-{scale}.json"
        self._reset_config(output_path)
        return output_path

    def identity_time(self, scale, output_path):
        # initialize a config from the identity transformation of time
        self.G = self.G * math.pow(scale, 2)
        self.per_step_time = self.per_step_time/scale
        self.v_norm = self.v_norm * scale 
        self.v_bias = self.v_bias * scale 
        self.metrics = self._get_metrics()
        output_path += f"-id-time-{scale}.json"
        self._reset_config(output_path)
        return output_path

    def identity_scope(self, scale, output_path):
        # initialize a config from the identity transformation of scope
        self.rho = self.rho * math.pow(scale, 3)
        self.sun_mass = self.sun_mass * math.pow(scale, 3)
        self.merging_threshold = self.merging_threshold * scale 
        
        self.pos_norm = self.pos_norm * scale 
        self.pos_bias = self.pos_bias * scale 
        self.v_norm = self.v_norm * scale
        self.v_bias = self.v_bias * scale
        self.metrics = self._get_metrics()
        output_path += f"-id-scope-{scale}.json"
        self._reset_config(output_path)
        return output_path

if __name__ == "__main__":
    basic_config = Params(basic_config_path).dict
    output_path = "./config/auto-config"
    scale = 4
    A = AutoConfig(basic_config)
    A.identity_length(scale, output_path)
        

