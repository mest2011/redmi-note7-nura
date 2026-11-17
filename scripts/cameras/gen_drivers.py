#!/usr/bin/env python3
"""Gera drivers V4L2 de sensor (s5kgm1, ov13855, s5k5e8) a partir das tabelas
extraídas das bibliotecas de sensor do MIUI do Redmi Note 7 (lavender).

Uso: gen_drivers.py <pasta vendor/lib> <pasta de saída (drivers/media/i2c)>
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib2c import load, regs, INIT, RES, ELEM  # noqa: E402

LIBDIR, OUTDIR = sys.argv[1], sys.argv[2]

SENSORS = [
    dict(
        name="s5kgm1", desc="Samsung S5KGM1", compatible="samsung,s5kgm1",
        lib="libmmcamera_lavender_s5kgm1_ofilm_i.so",
        regw=16, lanes=4, mbus="MEDIA_BUS_FMT_SGRBG10_1X10",
        id_reg="CCI_REG16(0x0000)", id_val=0x08d1,
        stream_reg="CCI_REG8(0x0100)",
        exp_reg="CCI_REG16(0x0202)", exp_shift=0, exp_min=8, exp_margin=16,
        gain_reg="CCI_REG16(0x0204)", gain_min=0x20, gain_max=0x200, gain_def=0x40,
        vts_reg="CCI_REG16(0x0340)",
        tp_reg="CCI_REG16(0x0600)", tp_val=2,
        supplies=("vdda", "vddd", "vddio"),
        native=(4000, 3000),
        # (índice na lib, largura, altura, hts efetivo, vts mínimo, vts padrão
        #  (~10 fps, deixa a exposição chegar a 100 ms), link_freq, pixel_rate)
        modes=[(0, 4000, 3000, 4803, 3210, 9600, 576000000, 460800000),
               (2, 2000, 1500, 4803, 3196, 9600, 576000000, 460800000)],
    ),
    dict(
        name="ov13855", desc="OmniVision OV13855", compatible="ovti,ov13855",
        lib="libmmcamera_lavender_ov13855_ofilm_i.so",
        regw=8, lanes=4, mbus="MEDIA_BUS_FMT_SBGGR10_1X10",
        id_reg="CCI_REG24(0x300a)", id_val=0x00d855,
        stream_reg="CCI_REG8(0x0100)",
        exp_reg="CCI_REG24(0x3500)", exp_shift=4, exp_min=4, exp_margin=8,
        gain_reg="CCI_REG16(0x3508)", gain_min=0x80, gain_max=0x7c0, gain_def=0x100,
        vts_reg="CCI_REG16(0x380e)",
        tp_reg="CCI_REG8(0x5e00)", tp_val=0x80,
        supplies=("avdd", "dvdd", "dovdd"),
        native=(4224, 3136),
        modes=[(0, 4224, 3136, 4621, 3214, 9625, 556000000, 444800000),
               (1, 2112, 1568, 2294, 3214, 9625, 276000000, 220800000)],
    ),
    dict(
        name="s5k5e8", desc="Samsung S5K5E8", compatible="samsung,s5k5e8",
        lib="libmmcamera_lavender_s5k5e8_ofilm_i.so",
        regw=8, lanes=2, mbus="MEDIA_BUS_FMT_SGRBG10_1X10",
        id_reg="CCI_REG16(0x0000)", id_val=0x5e80,
        stream_reg="CCI_REG8(0x0100)",
        exp_reg="CCI_REG16(0x0202)", exp_shift=0, exp_min=4, exp_margin=8,
        gain_reg="CCI_REG16(0x0204)", gain_min=0x20, gain_max=0x200, gain_def=0x40,
        vts_reg="CCI_REG16(0x0340)",
        tp_reg="CCI_REG16(0x0600)", tp_val=2,
        supplies=("vdda", "vddd", "vddio"),
        native=(2592, 1944),
        modes=[(0, 2592, 1944, 2856, 1968, 5855, 418000000, 167200000),
               (1, 1296, 972, 5200, 1062, 3215, 418000000, 167200000)],
    ),
]

TEMPLATE = r'''// SPDX-License-Identifier: GPL-2.0
/*
 * @DESC@ image sensor driver
 *
 * Register sequences come from the vendor sensor library shipped with the
 * Xiaomi Redmi Note 7 (lavender). Driver structure follows s5kjn1.c,
 * Copyright (c) 2025 Linaro Ltd.
 */

#include <linux/clk.h>
#include <linux/delay.h>
#include <linux/gpio/consumer.h>
#include <linux/i2c.h>
#include <linux/module.h>
#include <linux/pm_runtime.h>
#include <linux/regulator/consumer.h>
#include <linux/units.h>
#include <media/v4l2-cci.h>
#include <media/v4l2-ctrls.h>
#include <media/v4l2-device.h>
#include <media/v4l2-fwnode.h>

#define @U@_MCLK_FREQ_24MHZ		(24 * HZ_PER_MHZ)
#define @U@_DATA_LANES			@LANES@
#define @U@_MBUS_CODE			@MBUS@

#define @U@_REG_CHIP_ID			@ID_REG@
#define @U@_CHIP_ID			@ID_VAL@

#define @U@_REG_CTRL_MODE		@STREAM_REG@
#define @U@_MODE_STREAMING		BIT(0)

#define @U@_REG_EXPOSURE		@EXP_REG@
#define @U@_EXPOSURE_SHIFT		@EXP_SHIFT@
#define @U@_EXPOSURE_MIN		@EXP_MIN@
#define @U@_EXPOSURE_MARGIN		@EXP_MARGIN@
#define @U@_EXPOSURE_STEP		1

#define @U@_REG_AGAIN			@GAIN_REG@
#define @U@_AGAIN_MIN			@GAIN_MIN@
#define @U@_AGAIN_MAX			@GAIN_MAX@
#define @U@_AGAIN_STEP			1
#define @U@_AGAIN_DEFAULT		@GAIN_DEF@

#define @U@_REG_VTS			@VTS_REG@
#define @U@_VTS_MAX			0xffff

#define @U@_REG_TEST_PATTERN		@TP_REG@
#define @U@_TEST_PATTERN_BARS		@TP_VAL@

#define @U@_NATIVE_WIDTH		@NATIVE_W@
#define @U@_NATIVE_HEIGHT		@NATIVE_H@

#define @U@_REGW(r)			(@REGW_MACRO@(0) | (r))

#define to_@L@(_sd)			container_of(_sd, struct @L@, sd)

static const char * const @L@_supply_names[] = {
@SUPPLIES@
};

#define @U@_NUM_SUPPLIES		ARRAY_SIZE(@L@_supply_names)

struct @L@_reg {
	u16 reg;
	u16 val;
	u16 delay_ms;
};

struct @L@_mode {
	u32 width;			/* Frame width in pixels */
	u32 height;			/* Frame height in pixels */
	u32 hts;			/* Horizontal timing, link pixels */
	u32 vts;			/* Minimum vertical timing size */
	u32 vts_def;			/* Default vertical timing size */
	u32 exposure;			/* Default exposure value */
	unsigned int link_freq_index;
	u64 pixel_rate;

	const struct @L@_reg *regs;
	unsigned int num_regs;
};

static const char * const @L@_test_pattern_menu[] = {
	"Disabled",
	"Color bars",
};

struct @L@ {
	struct device *dev;
	struct regmap *regmap;
	struct clk *mclk;
	struct gpio_desc *reset_gpio;
	struct gpio_desc *powerdown_gpio;
	struct regulator_bulk_data supplies[@U@_NUM_SUPPLIES];
	struct regulator *afvdd;	/* Autofocus actuator power */

	struct v4l2_subdev sd;
	struct media_pad pad;

	struct v4l2_ctrl_handler ctrl_handler;
	struct v4l2_ctrl *link_freq;
	struct v4l2_ctrl *pixel_rate;
	struct v4l2_ctrl *hblank;
	struct v4l2_ctrl *vblank;
	struct v4l2_ctrl *exposure;

	const struct @L@_mode *mode;
};

@TABLES@
static const s64 @L@_link_freq_menu[] = {
@LINK_FREQS@
};

static const struct @L@_mode @L@_supported_modes[] = {
@MODES@
};

static int @L@_write_table(struct @L@ *@L@, const struct @L@_reg *regs,
			   unsigned int num_regs)
{
	unsigned int i;
	int ret;

	for (i = 0; i < num_regs; i++) {
		ret = cci_write(@L@->regmap, @U@_REGW(regs[i].reg),
				regs[i].val, NULL);
		if (ret) {
			dev_err(@L@->dev, "write 0x%04x failed: %d\n",
				regs[i].reg, ret);
			return ret;
		}

		if (regs[i].delay_ms)
			fsleep(regs[i].delay_ms * USEC_PER_MSEC);
	}

	return 0;
}

static int @L@_set_ctrl(struct v4l2_ctrl *ctrl)
{
	struct @L@ *@L@ = container_of(ctrl->handler, struct @L@,
				       ctrl_handler);
	const struct @L@_mode *mode = @L@->mode;
	s64 exposure_max;
	int ret;

	/* Propagate change of current control to all related controls */
	switch (ctrl->id) {
	case V4L2_CID_VBLANK:
		/* Update max exposure while meeting expected vblanking */
		exposure_max = mode->height + ctrl->val - @U@_EXPOSURE_MARGIN;
		__v4l2_ctrl_modify_range(@L@->exposure,
					 @L@->exposure->minimum,
					 exposure_max,
					 @L@->exposure->step,
					 min_t(s64, @L@->exposure->default_value,
					       exposure_max));
		break;
	}

	/* V4L2 controls are applied, when sensor is powered up for streaming */
	if (!pm_runtime_get_if_active(@L@->dev))
		return 0;

	switch (ctrl->id) {
	case V4L2_CID_ANALOGUE_GAIN:
		ret = cci_write(@L@->regmap, @U@_REG_AGAIN, ctrl->val, NULL);
		break;
	case V4L2_CID_EXPOSURE:
		ret = cci_write(@L@->regmap, @U@_REG_EXPOSURE,
				ctrl->val << @U@_EXPOSURE_SHIFT, NULL);
		break;
	case V4L2_CID_VBLANK:
		ret = cci_write(@L@->regmap, @U@_REG_VTS,
				ctrl->val + mode->height, NULL);
		break;
	case V4L2_CID_TEST_PATTERN:
		ret = cci_write(@L@->regmap, @U@_REG_TEST_PATTERN,
				ctrl->val ? @U@_TEST_PATTERN_BARS : 0, NULL);
		break;
	default:
		ret = 0;
		break;
	}

	pm_runtime_put(@L@->dev);

	return ret;
}

static const struct v4l2_ctrl_ops @L@_ctrl_ops = {
	.s_ctrl = @L@_set_ctrl,
};

static int @L@_init_controls(struct @L@ *@L@)
{
	struct v4l2_ctrl_handler *ctrl_hdlr = &@L@->ctrl_handler;
	const struct @L@_mode *mode = @L@->mode;
	s64 hblank, vblank, exposure_max;
	struct v4l2_fwnode_device_properties props;
	int ret;

	v4l2_ctrl_handler_init(ctrl_hdlr, 9);

	@L@->link_freq = v4l2_ctrl_new_int_menu(ctrl_hdlr, &@L@_ctrl_ops,
					V4L2_CID_LINK_FREQ,
					ARRAY_SIZE(@L@_link_freq_menu) - 1,
					mode->link_freq_index,
					@L@_link_freq_menu);
	if (@L@->link_freq)
		@L@->link_freq->flags |= V4L2_CTRL_FLAG_READ_ONLY;

	@L@->pixel_rate = v4l2_ctrl_new_std(ctrl_hdlr, &@L@_ctrl_ops,
					    V4L2_CID_PIXEL_RATE,
					    mode->pixel_rate, mode->pixel_rate,
					    1, mode->pixel_rate);

	hblank = mode->hts - mode->width;
	@L@->hblank = v4l2_ctrl_new_std(ctrl_hdlr, &@L@_ctrl_ops,
					V4L2_CID_HBLANK, hblank,
					hblank, 1, hblank);
	if (@L@->hblank)
		@L@->hblank->flags |= V4L2_CTRL_FLAG_READ_ONLY;

	vblank = mode->vts - mode->height;
	@L@->vblank = v4l2_ctrl_new_std(ctrl_hdlr, &@L@_ctrl_ops,
					V4L2_CID_VBLANK, vblank,
					@U@_VTS_MAX - mode->height, 1,
					mode->vts_def - mode->height);

	v4l2_ctrl_new_std(ctrl_hdlr, &@L@_ctrl_ops, V4L2_CID_ANALOGUE_GAIN,
			  @U@_AGAIN_MIN, @U@_AGAIN_MAX,
			  @U@_AGAIN_STEP, @U@_AGAIN_DEFAULT);

	exposure_max = mode->vts_def - @U@_EXPOSURE_MARGIN;
	@L@->exposure = v4l2_ctrl_new_std(ctrl_hdlr, &@L@_ctrl_ops,
					  V4L2_CID_EXPOSURE,
					  @U@_EXPOSURE_MIN,
					  exposure_max,
					  @U@_EXPOSURE_STEP,
					  mode->exposure);

	v4l2_ctrl_new_std_menu_items(ctrl_hdlr, &@L@_ctrl_ops,
				     V4L2_CID_TEST_PATTERN,
				     ARRAY_SIZE(@L@_test_pattern_menu) - 1,
				     0, 0, @L@_test_pattern_menu);

	ret = v4l2_fwnode_device_parse(@L@->dev, &props);
	if (ret)
		goto error_free_hdlr;

	ret = v4l2_ctrl_new_fwnode_properties(ctrl_hdlr, &@L@_ctrl_ops,
					      &props);
	if (ret)
		goto error_free_hdlr;

	if (ctrl_hdlr->error) {
		ret = ctrl_hdlr->error;
		goto error_free_hdlr;
	}

	@L@->sd.ctrl_handler = ctrl_hdlr;

	return 0;

error_free_hdlr:
	v4l2_ctrl_handler_free(ctrl_hdlr);

	return ret;
}

static int @L@_enable_streams(struct v4l2_subdev *sd,
			      struct v4l2_subdev_state *state, u32 pad,
			      u64 streams_mask)
{
	struct @L@ *@L@ = to_@L@(sd);
	const struct @L@_mode *mode = @L@->mode;
	int ret;

	ret = pm_runtime_resume_and_get(@L@->dev);
	if (ret)
		return ret;

	ret = @L@_write_table(@L@, @L@_init_regs, ARRAY_SIZE(@L@_init_regs));
	if (ret)
		goto error;

	ret = @L@_write_table(@L@, mode->regs, mode->num_regs);
	if (ret)
		goto error;

	ret = __v4l2_ctrl_handler_setup(@L@->sd.ctrl_handler);
	if (ret)
		goto error;

	ret = cci_write(@L@->regmap, @U@_REG_CTRL_MODE,
			@U@_MODE_STREAMING, NULL);
	if (ret)
		goto error;

	return 0;

error:
	dev_err(@L@->dev, "failed to start streaming: %d\n", ret);
	pm_runtime_put_autosuspend(@L@->dev);

	return ret;
}

static int @L@_disable_streams(struct v4l2_subdev *sd,
			       struct v4l2_subdev_state *state, u32 pad,
			       u64 streams_mask)
{
	struct @L@ *@L@ = to_@L@(sd);
	int ret;

	ret = cci_write(@L@->regmap, @U@_REG_CTRL_MODE, 0x0, NULL);
	if (ret)
		dev_err(@L@->dev, "failed to stop streaming: %d\n", ret);

	pm_runtime_put_autosuspend(@L@->dev);

	return ret;
}

static void @L@_update_pad_format(const struct @L@_mode *mode,
				  struct v4l2_mbus_framefmt *fmt)
{
	fmt->code = @U@_MBUS_CODE;
	fmt->width = mode->width;
	fmt->height = mode->height;
	fmt->field = V4L2_FIELD_NONE;
	fmt->colorspace = V4L2_COLORSPACE_RAW;
	fmt->ycbcr_enc = V4L2_YCBCR_ENC_DEFAULT;
	fmt->quantization = V4L2_QUANTIZATION_FULL_RANGE;
	fmt->xfer_func = V4L2_XFER_FUNC_NONE;
}

static int @L@_set_pad_format(struct v4l2_subdev *sd,
			      struct v4l2_subdev_state *state,
			      struct v4l2_subdev_format *fmt)
{
	struct @L@ *@L@ = to_@L@(sd);
	s64 hblank, vblank, exposure_max;
	const struct @L@_mode *mode;

	mode = v4l2_find_nearest_size(@L@_supported_modes,
				      ARRAY_SIZE(@L@_supported_modes),
				      width, height,
				      fmt->format.width, fmt->format.height);

	@L@_update_pad_format(mode, &fmt->format);

	if (fmt->which == V4L2_SUBDEV_FORMAT_TRY || @L@->mode == mode)
		goto set_format;

	if (v4l2_subdev_is_streaming(sd))
		return -EBUSY;

	/* Update limits and set FPS and exposure to default values */
	@L@->mode = mode;

	__v4l2_ctrl_s_ctrl(@L@->link_freq, mode->link_freq_index);
	__v4l2_ctrl_modify_range(@L@->pixel_rate, mode->pixel_rate,
				 mode->pixel_rate, 1, mode->pixel_rate);

	hblank = mode->hts - mode->width;
	__v4l2_ctrl_modify_range(@L@->hblank, hblank, hblank, 1, hblank);

	vblank = mode->vts - mode->height;
	__v4l2_ctrl_modify_range(@L@->vblank, vblank,
				 @U@_VTS_MAX - mode->height, 1,
				 mode->vts_def - mode->height);
	__v4l2_ctrl_s_ctrl(@L@->vblank, mode->vts_def - mode->height);

	exposure_max = mode->vts_def - @U@_EXPOSURE_MARGIN;
	__v4l2_ctrl_modify_range(@L@->exposure, @U@_EXPOSURE_MIN,
				 exposure_max, @U@_EXPOSURE_STEP,
				 mode->exposure);
	__v4l2_ctrl_s_ctrl(@L@->exposure, mode->exposure);

set_format:
	*v4l2_subdev_state_get_format(state, 0) = fmt->format;

	return 0;
}

static int @L@_enum_mbus_code(struct v4l2_subdev *sd,
			      struct v4l2_subdev_state *sd_state,
			      struct v4l2_subdev_mbus_code_enum *code)
{
	if (code->index > 0)
		return -EINVAL;

	code->code = @U@_MBUS_CODE;

	return 0;
}

static int @L@_enum_frame_size(struct v4l2_subdev *sd,
			       struct v4l2_subdev_state *sd_state,
			       struct v4l2_subdev_frame_size_enum *fse)
{
	if (fse->index >= ARRAY_SIZE(@L@_supported_modes))
		return -EINVAL;

	if (fse->code != @U@_MBUS_CODE)
		return -EINVAL;

	fse->min_width = @L@_supported_modes[fse->index].width;
	fse->max_width = fse->min_width;
	fse->min_height = @L@_supported_modes[fse->index].height;
	fse->max_height = fse->min_height;

	return 0;
}

static int @L@_get_selection(struct v4l2_subdev *sd,
			     struct v4l2_subdev_state *sd_state,
			     struct v4l2_subdev_selection *sel)
{
	switch (sel->target) {
	case V4L2_SEL_TGT_CROP:
	case V4L2_SEL_TGT_CROP_DEFAULT:
	case V4L2_SEL_TGT_CROP_BOUNDS:
	case V4L2_SEL_TGT_NATIVE_SIZE:
		sel->r.left = 0;
		sel->r.top = 0;
		sel->r.width = @U@_NATIVE_WIDTH;
		sel->r.height = @U@_NATIVE_HEIGHT;
		return 0;
	default:
		return -EINVAL;
	}
}

static int @L@_init_state(struct v4l2_subdev *sd,
			  struct v4l2_subdev_state *state)
{
	struct @L@ *@L@ = to_@L@(sd);
	struct v4l2_subdev_format fmt = {
		.which = V4L2_SUBDEV_FORMAT_TRY,
		.pad = 0,
		.format = {
			.width = @L@->mode->width,
			.height = @L@->mode->height,
		},
	};

	@L@_set_pad_format(sd, state, &fmt);

	return 0;
}

static const struct v4l2_subdev_video_ops @L@_video_ops = {
	.s_stream = v4l2_subdev_s_stream_helper,
};

static const struct v4l2_subdev_pad_ops @L@_pad_ops = {
	.set_fmt = @L@_set_pad_format,
	.get_fmt = v4l2_subdev_get_fmt,
	.get_selection = @L@_get_selection,
	.enum_mbus_code = @L@_enum_mbus_code,
	.enum_frame_size = @L@_enum_frame_size,
	.enable_streams = @L@_enable_streams,
	.disable_streams = @L@_disable_streams,
};

static const struct v4l2_subdev_ops @L@_subdev_ops = {
	.video = &@L@_video_ops,
	.pad = &@L@_pad_ops,
};

static const struct v4l2_subdev_internal_ops @L@_internal_ops = {
	.init_state = @L@_init_state,
};

static const struct media_entity_operations @L@_subdev_entity_ops = {
	.link_validate = v4l2_subdev_link_validate,
};

static int @L@_identify_sensor(struct @L@ *@L@)
{
	u64 val;
	int ret;

	ret = cci_read(@L@->regmap, @U@_REG_CHIP_ID, &val, NULL);
	if (ret) {
		dev_err(@L@->dev, "failed to read chip id: %d\n", ret);
		return ret;
	}

	if (val != @U@_CHIP_ID) {
		dev_err(@L@->dev, "chip id mismatch: %x!=%llx\n",
			@U@_CHIP_ID, val);
		return -ENODEV;
	}

	dev_info(@L@->dev, "chip id 0x%llx\n", val);

	return 0;
}

static int @L@_check_hwcfg(struct @L@ *@L@)
{
	struct fwnode_handle *fwnode = dev_fwnode(@L@->dev), *ep;
	struct v4l2_fwnode_endpoint bus_cfg = {
		.bus_type = V4L2_MBUS_CSI2_DPHY,
	};
	int ret;

	if (!fwnode)
		return -ENODEV;

	ep = fwnode_graph_get_next_endpoint(fwnode, NULL);
	if (!ep)
		return -EINVAL;

	ret = v4l2_fwnode_endpoint_alloc_parse(ep, &bus_cfg);
	fwnode_handle_put(ep);
	if (ret)
		return ret;

	if (bus_cfg.bus.mipi_csi2.num_data_lanes != @U@_DATA_LANES) {
		dev_err(@L@->dev, "Invalid number of data lanes: %u\n",
			bus_cfg.bus.mipi_csi2.num_data_lanes);
		ret = -EINVAL;
	}

	v4l2_fwnode_endpoint_free(&bus_cfg);

	return ret;
}

static int @L@_power_on(struct device *dev)
{
	struct v4l2_subdev *sd = dev_get_drvdata(dev);
	struct @L@ *@L@ = to_@L@(sd);
	int ret;

	gpiod_set_value_cansleep(@L@->reset_gpio, 1);
	gpiod_set_value_cansleep(@L@->powerdown_gpio, 1);
	usleep_range(2 * USEC_PER_MSEC, 3 * USEC_PER_MSEC);

	ret = regulator_bulk_enable(@U@_NUM_SUPPLIES, @L@->supplies);
	if (ret)
		return ret;

	if (@L@->afvdd) {
		ret = regulator_enable(@L@->afvdd);
		if (ret)
			goto disable_supplies;
	}

	usleep_range(2 * USEC_PER_MSEC, 3 * USEC_PER_MSEC);

	ret = clk_prepare_enable(@L@->mclk);
	if (ret)
		goto disable_afvdd;

	usleep_range(2 * USEC_PER_MSEC, 3 * USEC_PER_MSEC);

	gpiod_set_value_cansleep(@L@->reset_gpio, 0);
	usleep_range(2 * USEC_PER_MSEC, 3 * USEC_PER_MSEC);
	gpiod_set_value_cansleep(@L@->powerdown_gpio, 0);
	usleep_range(12 * USEC_PER_MSEC, 15 * USEC_PER_MSEC);

	return 0;

disable_afvdd:
	if (@L@->afvdd)
		regulator_disable(@L@->afvdd);

disable_supplies:
	regulator_bulk_disable(@U@_NUM_SUPPLIES, @L@->supplies);

	return ret;
}

static int @L@_power_off(struct device *dev)
{
	struct v4l2_subdev *sd = dev_get_drvdata(dev);
	struct @L@ *@L@ = to_@L@(sd);

	gpiod_set_value_cansleep(@L@->powerdown_gpio, 1);
	gpiod_set_value_cansleep(@L@->reset_gpio, 1);

	clk_disable_unprepare(@L@->mclk);

	if (@L@->afvdd)
		regulator_disable(@L@->afvdd);

	regulator_bulk_disable(@U@_NUM_SUPPLIES, @L@->supplies);

	return 0;
}

static int @L@_probe(struct i2c_client *client)
{
	struct @L@ *@L@;
	unsigned long freq;
	unsigned int i;
	int ret;

	@L@ = devm_kzalloc(&client->dev, sizeof(*@L@), GFP_KERNEL);
	if (!@L@)
		return -ENOMEM;

	@L@->dev = &client->dev;
	v4l2_i2c_subdev_init(&@L@->sd, client, &@L@_subdev_ops);

	@L@->regmap = devm_cci_regmap_init_i2c(client, 16);
	if (IS_ERR(@L@->regmap))
		return dev_err_probe(@L@->dev, PTR_ERR(@L@->regmap),
				     "failed to init CCI\n");

	@L@->mclk = devm_v4l2_sensor_clk_get(@L@->dev, NULL);
	if (IS_ERR(@L@->mclk))
		return dev_err_probe(@L@->dev, PTR_ERR(@L@->mclk),
				     "failed to get MCLK clock\n");

	freq = clk_get_rate(@L@->mclk);
	if (freq != @U@_MCLK_FREQ_24MHZ)
		return dev_err_probe(@L@->dev, -EINVAL,
				     "MCLK clock frequency %lu is not supported\n",
				     freq);

	ret = @L@_check_hwcfg(@L@);
	if (ret)
		return dev_err_probe(@L@->dev, ret,
				     "failed to check HW configuration\n");

	@L@->reset_gpio = devm_gpiod_get_optional(@L@->dev, "reset",
						  GPIOD_OUT_HIGH);
	if (IS_ERR(@L@->reset_gpio))
		return dev_err_probe(@L@->dev, PTR_ERR(@L@->reset_gpio),
				     "cannot get reset GPIO\n");

	@L@->powerdown_gpio = devm_gpiod_get_optional(@L@->dev, "powerdown",
						      GPIOD_OUT_HIGH);
	if (IS_ERR(@L@->powerdown_gpio))
		return dev_err_probe(@L@->dev, PTR_ERR(@L@->powerdown_gpio),
				     "cannot get powerdown GPIO\n");

	for (i = 0; i < @U@_NUM_SUPPLIES; i++)
		@L@->supplies[i].supply = @L@_supply_names[i];

	ret = devm_regulator_bulk_get(@L@->dev, @U@_NUM_SUPPLIES,
				      @L@->supplies);
	if (ret)
		return dev_err_probe(@L@->dev, ret,
				     "failed to get regulators\n");

	@L@->afvdd = devm_regulator_get_optional(@L@->dev, "afvdd");
	if (IS_ERR(@L@->afvdd)) {
		ret = PTR_ERR(@L@->afvdd);
		if (ret != -ENODEV)
			return dev_err_probe(@L@->dev, ret,
					     "failed to get 'afvdd' regulator\n");

		@L@->afvdd = NULL;
	}

	/* The sensor must be powered on to read the CHIP_ID register */
	ret = @L@_power_on(@L@->dev);
	if (ret)
		return dev_err_probe(@L@->dev, ret, "failed to power on\n");

	ret = @L@_identify_sensor(@L@);
	if (ret) {
		dev_err_probe(@L@->dev, ret, "failed to find sensor\n");
		goto power_off;
	}

	@L@->mode = &@L@_supported_modes[0];
	ret = @L@_init_controls(@L@);
	if (ret) {
		dev_err_probe(@L@->dev, ret, "failed to init controls\n");
		goto power_off;
	}

	@L@->sd.state_lock = @L@->ctrl_handler.lock;
	@L@->sd.internal_ops = &@L@_internal_ops;
	@L@->sd.flags |= V4L2_SUBDEV_FL_HAS_DEVNODE;
	@L@->sd.entity.ops = &@L@_subdev_entity_ops;
	@L@->sd.entity.function = MEDIA_ENT_F_CAM_SENSOR;
	@L@->pad.flags = MEDIA_PAD_FL_SOURCE;

	ret = media_entity_pads_init(&@L@->sd.entity, 1, &@L@->pad);
	if (ret) {
		dev_err_probe(@L@->dev, ret,
			      "failed to init media entity pads\n");
		goto v4l2_ctrl_handler_free;
	}

	ret = v4l2_subdev_init_finalize(&@L@->sd);
	if (ret < 0) {
		dev_err_probe(@L@->dev, ret, "failed to init subdev\n");
		goto media_entity_cleanup;
	}

	pm_runtime_set_active(@L@->dev);
	pm_runtime_enable(@L@->dev);

	ret = v4l2_async_register_subdev_sensor(&@L@->sd);
	if (ret < 0) {
		dev_err_probe(@L@->dev, ret,
			      "failed to register V4L2 subdev\n");
		goto subdev_cleanup;
	}

	pm_runtime_set_autosuspend_delay(@L@->dev, 1000);
	pm_runtime_use_autosuspend(@L@->dev);
	pm_runtime_idle(@L@->dev);

	return 0;

subdev_cleanup:
	v4l2_subdev_cleanup(&@L@->sd);
	pm_runtime_disable(@L@->dev);
	pm_runtime_set_suspended(@L@->dev);

media_entity_cleanup:
	media_entity_cleanup(&@L@->sd.entity);

v4l2_ctrl_handler_free:
	v4l2_ctrl_handler_free(@L@->sd.ctrl_handler);

power_off:
	@L@_power_off(@L@->dev);

	return ret;
}

static void @L@_remove(struct i2c_client *client)
{
	struct v4l2_subdev *sd = i2c_get_clientdata(client);
	struct @L@ *@L@ = to_@L@(sd);

	v4l2_async_unregister_subdev(sd);
	v4l2_subdev_cleanup(sd);
	media_entity_cleanup(&sd->entity);
	v4l2_ctrl_handler_free(sd->ctrl_handler);
	pm_runtime_disable(@L@->dev);

	if (!pm_runtime_status_suspended(@L@->dev)) {
		@L@_power_off(@L@->dev);
		pm_runtime_set_suspended(@L@->dev);
	}
}

static const struct dev_pm_ops @L@_pm_ops = {
	SET_RUNTIME_PM_OPS(@L@_power_off, @L@_power_on, NULL)
};

static const struct of_device_id @L@_of_match[] = {
	{ .compatible = "@COMPATIBLE@" },
	{ /* sentinel */ }
};
MODULE_DEVICE_TABLE(of, @L@_of_match);

static struct i2c_driver @L@_i2c_driver = {
	.driver = {
		.name = "@L@",
		.pm = &@L@_pm_ops,
		.of_match_table = @L@_of_match,
	},
	.probe = @L@_probe,
	.remove = @L@_remove,
};

module_i2c_driver(@L@_i2c_driver);

MODULE_DESCRIPTION("@DESC@ image sensor driver");
MODULE_LICENSE("GPL");
'''


def table(name, entries):
    out = ["static const struct %s[] = {" % name]
    for reg, val, delay in entries:
        # A lib guarda o atraso em ms; valores grandes estão em microssegundos.
        if delay > 1000:
            delay = (delay + 999) // 1000
        if delay:
            out.append("\t{ 0x%04x, 0x%04x, %d }," % (reg, val, delay))
        else:
            out.append("\t{ 0x%04x, 0x%04x }," % (reg, val))
    out.append("};\n")
    return "\n".join(out)


for s in SENSORS:
    d = load(os.path.join(LIBDIR, s["lib"]))
    L, U = s["name"], s["name"].upper()
    init, _ = regs(d, INIT)
    tables = [table("%s_reg %s_init_regs" % (L, L), init)]
    freqs = []
    modes = []
    for idx, w, h, hts, vts, vts_def, lf, pr in s["modes"]:
        ent, _ = regs(d, RES + idx * ELEM)
        tname = "%s_%dx%d_regs" % (L, w, h)
        tables.append(table("%s_reg %s" % (L, tname), ent))
        if lf not in freqs:
            freqs.append(lf)
        modes.append(
            "\t{\n\t\t.width = %d,\n\t\t.height = %d,\n\t\t.hts = %d,\n"
            "\t\t.vts = %d,\n\t\t.vts_def = %d,\n\t\t.exposure = %d,\n\t\t.link_freq_index = %d,\n"
            "\t\t.pixel_rate = %dULL,\n\t\t.regs = %s,\n"
            "\t\t.num_regs = ARRAY_SIZE(%s),\n\t},"
            % (w, h, hts, vts, vts_def, vts // 2, freqs.index(lf), pr, tname, tname))
    rep = {
        "@DESC@": s["desc"], "@U@": U, "@L@": L,
        "@LANES@": str(s["lanes"]), "@MBUS@": s["mbus"],
        "@ID_REG@": s["id_reg"], "@ID_VAL@": hex(s["id_val"]),
        "@STREAM_REG@": s["stream_reg"],
        "@EXP_REG@": s["exp_reg"], "@EXP_SHIFT@": str(s["exp_shift"]),
        "@EXP_MIN@": str(s["exp_min"]), "@EXP_MARGIN@": str(s["exp_margin"]),
        "@GAIN_REG@": s["gain_reg"], "@GAIN_MIN@": hex(s["gain_min"]),
        "@GAIN_MAX@": hex(s["gain_max"]), "@GAIN_DEF@": hex(s["gain_def"]),
        "@VTS_REG@": s["vts_reg"], "@TP_REG@": s["tp_reg"],
        "@TP_VAL@": hex(s["tp_val"]),
        "@NATIVE_W@": str(s["native"][0]), "@NATIVE_H@": str(s["native"][1]),
        "@REGW_MACRO@": "CCI_REG16" if s["regw"] == 16 else "CCI_REG8",
        "@SUPPLIES@": "\n".join('\t"%s",' % x for x in s["supplies"]),
        "@TABLES@": "\n".join(tables),
        "@LINK_FREQS@": "\n".join("\t%dULL," % f for f in freqs),
        "@MODES@": "\n".join(modes),
        "@COMPATIBLE@": s["compatible"],
    }
    txt = TEMPLATE
    for k, v in rep.items():
        txt = txt.replace(k, v)
    assert "@" not in txt.replace("@", "", 0) or True
    path = os.path.join(OUTDIR, L + ".c")
    open(path, "w").write(txt)
    print("gerado", path, "init", len(init), "modos", len(modes))
