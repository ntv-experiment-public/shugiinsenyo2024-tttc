import { Zoom } from '@/hooks/useZoom';
import { Point, Dimensions } from '@/types';
import { CSSProperties, useState } from 'react';
import { ThumbUp, ThumbDown } from '@/icons';
import { Translator } from '@/hooks/useTranslatorAndReplacements';
import VideoLink from './VideoLink';

type TooltipProps = {
  point: Point,
  dimensions: Dimensions
  expanded: boolean,
  zoom: Zoom,
  fullScreen?: boolean,
  translator: Translator
}

const Tooltip = ({ point, dimensions, expanded, zoom, fullScreen, translator }: TooltipProps) => {
  const { scaleX, scaleY, width, height } = dimensions;
  const [showMoreComment, setShowMoreComment] = useState(false)
  const { zoomX, zoomY } = zoom;
  const x = zoomX(scaleX(point.x))
  const y = zoomY(scaleY(point.y))
  const { t } = translator

  let style: CSSProperties = {}
  if (!fullScreen) {
    style = {
      left: width - 20,
      top: -20,
      height: expanded ? height : 'auto',
      overflowY: expanded ? 'auto' : 'hidden',
    }

  } else if (expanded) {
    style = {
      ...(x > width / 2 ? { right: width - x } : { left: x }),
      top: 0,
      height: dimensions.height - 40,
      overflowY: 'auto',
    }
  } else {
    style = {
      ...(x > width / 2 ? { right: width - x } : { left: x }),
      ...(y > height / 2 ? { bottom: height - y } : { top: y }),
      pointerEvents: 'none',
    }
  }

  return <div
    className='text-left absolute p-4 bg-blue-100 shadow-sm m-5 w-[430px] transition-all duration-300'
    style={style}>
    <div
      className='text-sm font-bold'
      style={{ color: point.color }}>
      {t(point.cluster)}
    </div>
    <div className='text-lg my-2'>
      {t(point.argument)}
    </div>
    {(point.agrees || point.disagrees) && <div className='text-sm opacity-80 mb-2 font-bold'>
      <ThumbUp className='w-4 inline-block' /> {point.agrees}
      <ThumbDown className='w-4 inline-block ml-3' />  {point.disagrees}
    </div>
    }
    <VideoLink {...point} showVideo={false}  showThumbnail={!expanded} />
  </div>
}

export default Tooltip;
